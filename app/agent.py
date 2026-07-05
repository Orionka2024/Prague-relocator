import datetime
import json
import re
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.workflow import Workflow, node, START
from google.genai import types
from mcp import StdioServerParameters
from app.config import config

# Setup MCP Toolset running as a stdio subprocess
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "app.mcp_server"],
        )
    )
)

# Sub-agents with MCP Toolset wired in
visa_expert = LlmAgent(
    name="visa_expert",
    model=config.model,
    instruction="""You are the Prague Visa & Immigration Expert.
Your task is to help the user identify the correct Czech visa or residence permit, provide document checklists, and outline the application steps based on official Ministry of Interior (MVCR) rules.
You have access to the mcp_toolset to retrieve requirements, documents, and office locations. Always use these tools to ensure accuracy!
""",
    tools=[mcp_toolset],
    description="Visa and immigration specialist. Use this for visa options, required documents, consulate/embassy locations, and deadlines."
)

settling_expert = LlmAgent(
    name="settling_expert",
    model=config.model,
    instruction="""You are the Prague Settling-In Expert.
Your task is to help the user with health insurance, accommodation registration, Foreign Police visits, public transport, and practical aspects of living in Prague.
You have access to the mcp_toolset to retrieve office locations and health insurance requirements. Always use these tools to ensure accuracy!
""",
    tools=[mcp_toolset],
    description="Settling-in and local administration specialist. Use this for health insurance requirements, address registration, foreign police offices, and public transport."
)

# Orchestrator agent delegating to the specialists
orchestrator = LlmAgent(
    name="orchestrator",
    model=config.model,
    instruction="""You are the Prague Relocator Orchestrator.
Your goal is to help the user relocate to Prague.
The user's nationality is: {nationality}
The user's purpose of stay is: {purpose}

You have access to two specialized expert sub-agents:
1. visa_expert: Deals with visa options, checklists, application procedures, and embassies.
2. settling_expert: Deals with health insurance, housing registration, foreign police, and local Prague lifestyle.

Examine the user's query and delegate to the appropriate sub-agent using their tool.
If the query requires both, you can call them sequentially.
Summarize the expert's response and provide a clear, welcoming, and actionable response to the user.
""",
    tools=[AgentTool(visa_expert), AgentTool(settling_expert)]
)

# Workflow Function Nodes

@node
def security_checkpoint(ctx: Context, node_input: types.Content) -> Event:
    text = ""
    if isinstance(node_input, str):
        text = node_input
    elif hasattr(node_input, 'parts') and node_input.parts:
        text = "".join(part.text for part in node_input.parts if part.text)
    elif isinstance(node_input, dict) and "parts" in node_input:
        text = "".join(p.get("text", "") for p in node_input["parts"] if isinstance(p, dict))

    # 1. PII scrubbing
    passport_pattern = r'[A-Z0-9]{8,9}'
    birth_date_pattern = r'\b\d{2}[\./-]\d{2}[\./-]\d{4}\b'
    phone_pattern = r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{3,4}'
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    scrubbed_text = text
    if config.pii_redaction_enabled:
        scrubbed_text = re.sub(passport_pattern, "[REDACTED_PASSPORT]", scrubbed_text)
        scrubbed_text = re.sub(birth_date_pattern, "[REDACTED_DATE]", scrubbed_text)
        scrubbed_text = re.sub(phone_pattern, "[REDACTED_PHONE]", scrubbed_text)
        scrubbed_text = re.sub(email_pattern, "[REDACTED_EMAIL]", scrubbed_text)

    # 2. Prompt injection keyword detection -> SECURITY_EVENT route
    is_injection = False
    if config.injection_detection_enabled:
        injection_keywords = ["ignore previous instructions", "system prompt", "you are now", "jailbreak", "bypass security"]
        is_injection = any(kw in text.lower() for kw in injection_keywords)
    
    # 3. Domain-specific compliance check (prevent illegal advice/migration)
    illegal_keywords = ["illegal entry", "cross border illegally", "work illegally", "work without permit", "fake document"]
    is_illegal_intent = any(kw in text.lower() for kw in illegal_keywords)

    audit_log = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "session_id": ctx.session.id,
        "pii_redacted": scrubbed_text != text,
        "prompt_injection_detected": is_injection,
        "illegal_intent_detected": is_illegal_intent
    }

    if is_injection or is_illegal_intent:
        severity = "CRITICAL" if is_injection else "WARNING"
        print(json.dumps({"severity": severity, "message": "Security policy violation", "audit_log": audit_log}))
        return Event(output="Security policy violation detected. Request blocked.", route="SECURITY_EVENT")

    print(json.dumps({"severity": "INFO", "message": "Security check passed", "audit_log": audit_log}))
    return Event(output=scrubbed_text, route="CLEAN", state={"scrubbed_input": scrubbed_text})

@node
def security_event_handler(ctx: Context, node_input: str):
    yield Event(content=types.Content(role='model', parts=[types.Part.from_text(text=node_input)]))
    yield Event(output=node_input)

@node(rerun_on_resume=True)
async def input_collector(ctx: Context, node_input: str):
    nationality = ctx.state.get("nationality")
    purpose = ctx.state.get("purpose")
    
    if ctx.resume_inputs:
        if "nationality_input" in ctx.resume_inputs:
            nationality = ctx.resume_inputs["nationality_input"]
            ctx.state["nationality"] = nationality
        if "purpose_input" in ctx.resume_inputs:
            purpose = ctx.resume_inputs["purpose_input"]
            ctx.state["purpose"] = purpose

    if not nationality:
        yield RequestInput(
            interrupt_id="nationality_input",
            message="Ahoj! Welcome to Prague Relocator. To help you better, what is your nationality?"
        )
        return

    if not purpose:
        yield RequestInput(
            interrupt_id="purpose_input",
            message=f"Got it, you are a citizen of {nationality}. What is your purpose of stay in Prague? (e.g., study, work, business, digital nomad)"
        )
        return

    yield Event(output=node_input, route="PROCEED")

@node
def final_output(ctx: Context, node_input: types.Content):
    text = ""
    if isinstance(node_input, str):
        text = node_input
    elif hasattr(node_input, 'parts') and node_input.parts:
        text = "".join(part.text for part in node_input.parts if part.text)
    
    yield Event(content=types.Content(role='model', parts=[types.Part.from_text(text=text)]))
    yield Event(output=text)

# Root agent Workflow construction
root_agent = Workflow(
    name="prague_relocator_workflow",
    edges=[
        ('START', security_checkpoint),
        (security_checkpoint, {"SECURITY_EVENT": security_event_handler, "CLEAN": input_collector}),
        (input_collector, {"PROCEED": orchestrator}),
        (orchestrator, final_output)
    ]
)

# App wrapping
app = App(
    root_agent=root_agent,
    name="app",
)

# Prague Relocator

Prague Relocator is a secure, multi-agent AI assistant designed to guide foreigners through the visa, immigration, and settling-in processes in Prague using official Czech government guidelines.

## Prerequisites

* Python 3.11+
* [uv](https://docs.astral.sh/uv/) (Python package manager)
* Gemini API Key (Get one from [Google AI Studio](https://aistudio.google.com/apikey))

## Quick Start

```bash
git clone <repo-url>
cd prague-relocator
cp .env.example .env   # Add your GOOGLE_API_KEY
make install
make playground        # Opens the UI at http://localhost:18081
```

## Architecture

```mermaid
graph TD
    START[User Message] --> SC[Security Checkpoint]
    SC -- Violation --> SE[Security Event Handler]
    SC -- Clean --> IC[Input Collector (HITL)]
    IC -- Proceed --> OR[Orchestrator Agent]
    OR --> VE[Visa Expert Agent]
    OR --> SE_EXP[Settling Expert Agent]
    VE --> MCP[MCP Server: Visa & Document Tools]
    SE_EXP --> MCP
    OR --> FO[Final Output]
```

## How to Run

* **`make playground`**: Runs the interactive developer playground UI at `http://localhost:18081`. Use this to test the agent, inspect step-by-step trace logs, and try different user inputs.
* **`make run`**: Runs the API server locally on port 8000. Useful for backend integration tests.

## Sample Test Cases

### Test Case 1: Student Visa Path (Non-EU)
* **Input**: `"Hi, I am looking to move to Prague."`
* **Expected**: 
  1. Security Checkpoint passes.
  2. Input Collector interrupts and asks for Nationality.
  3. Respond: `"Indian"`. Input Collector asks for Purpose.
  4. Respond: `"Study"`. Input Collector yields Proceed.
  5. Orchestrator calls `visa_expert`.
  6. `visa_expert` calls `get_visa_requirements` and `get_required_documents` on MCP.
  7. Returns study visa recommendations and document checklists (translation required, funds proof, study confirmation).
* **Check**: You see the step-by-step user-prompted inputs in the Playground chat, and the final response lists student visa details.

### Test Case 2: Business Visa (Živnostenský list)
* **Input**: `"I want to work as a freelance developer in Prague. My nationality is USA."`
* **Expected**:
  1. Input Collector sees Nationality (USA) and Purpose (Business/Freelance) are in the input, skips prompts.
  2. Orchestrator calls `visa_expert`.
  3. `visa_expert` queries MCP for Business visa requirements.
  4. Returns info on Trade License ("Živno"), required registration documents, and funding requirements.
* **Check**: The orchestrator responds immediately with Živno details without interrupting for input.

### Test Case 3: Health Insurance Query
* **Input**: `"I have already arrived in Prague on a student visa. What insurance do I need, and where is the Foreign Police?"`
* **Expected**:
  1. Input Collector asks for nationality if not in session state.
  2. Once answered, Orchestrator routes the health insurance and Foreign Police queries to `settling_expert`.
  3. `settling_expert` calls MCP `get_health_insurance_info` and `get_office_locations` (police).
  4. Returns comprehensive insurance guidelines (pVZP / commercial health coverage) and the Olšanská 2176/2 Foreign Police address.
* **Check**: Output includes Olšanská address and comprehensive pVZP insurance requirements.

## Troubleshooting

1. **Model 404 / 403 Errors**:
   * Ensure `GEMINI_MODEL=gemini-2.5-flash` is set in your `.env`.
   * Make sure your `GOOGLE_API_KEY` is active and correct.
2. **"no agents found" / "extra arguments" on Startup**:
   * Make sure you are in the `prague-relocator` project root directory when running `make playground`.
3. **Stale Code Changes on Windows**:
   * Windows hot-reload does not automatically pick up python file edits. Make sure to terminate the running server using Ctrl+C (or kill port 18081) and relaunch using `make playground`.

## Push to GitHub

1. Create a new repo at https://github.com/new
   * Name: prague-relocator
   * Visibility: Public or Private
   * Do NOT initialize with README (you already have one)

2. In your terminal, navigate into your project folder:
   ```bash
   cd prague-relocator
   git init
   git add .
   git commit -m "Initial commit: prague-relocator ADK agent"
   git branch -M main
   git remote add origin https://github.com/<your-username>/prague-relocator.git
   git push -u origin main
   ```

3. Verify .gitignore includes:
   ```
   .env          # your API key — must NEVER be pushed
   .venv/
   __pycache__/
   *.pyc
   .adk/
   ```

⚠ NEVER push .env to GitHub. Your API key will be exposed publicly.

## Assets

* **Workflow Diagram**: [assets/architecture_diagram.png](file:///Users/aleksandrkim/Documents/ADK-Workspace/prague-relocator/assets/architecture_diagram.png)
* **Cover Banner**: [assets/cover_page_banner.png](file:///Users/aleksandrkim/Documents/ADK-Workspace/prague-relocator/assets/cover_page_banner.png)

## Demo Script

A conversational walkthrough script is available at [DEMO_SCRIPT.txt](file:///Users/aleksandrkim/Documents/ADK-Workspace/prague-relocator/DEMO_SCRIPT.txt).

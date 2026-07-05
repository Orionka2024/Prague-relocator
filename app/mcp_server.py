import logging
from mcp.server.fastmcp import FastMCP

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_prague_relocator")

mcp = FastMCP("Prague Relocation Services")

@mcp.tool()
def get_visa_requirements(nationality: str, purpose: str) -> dict:
    """Get visa/residence permit recommendations based on nationality and purpose of stay.

    Args:
        nationality: Country of citizenship (e.g. USA, Canada, India).
        purpose: Purpose of relocation (e.g. study, work, business, digital nomad).
    """
    logger.info(f"get_visa_requirements called for nationality={nationality}, purpose={purpose}")
    nationality_lower = nationality.lower()
    purpose_lower = purpose.lower()

    # Determine EU vs Non-EU
    eu_countries = {
        "austria", "belgium", "bulgaria", "croatia", "cyprus", "czech republic", "denmark",
        "estonia", "finland", "france", "germany", "greece", "hungary", "ireland", "italy",
        "latvia", "lithuania", "luxembourg", "malta", "netherlands", "poland", "portugal",
        "romania", "slovakia", "slovenia", "spain", "sweden"
    }
    is_eu = nationality_lower in eu_countries

    if is_eu:
        return {
            "is_eu": True,
            "permit_name": "Temporary Residence Certificate (Potvrzení o přechodném pobytu)",
            "description": "EU citizens do not need a visa to live or work in the Czech Republic. However, for stays longer than 30 days, registration with the Foreign Police is required. For stays longer than 90 days, applying for a Temporary Residence Certificate is recommended but optional.",
            "processing_time": "30-60 days",
            "next_steps": "1. Enter the Czech Republic with a valid passport/ID. 2. Register address at the Foreign Police within 30 days. 3. Apply for Temporary Residence at the MVCR if staying long-term."
        }

    # Non-EU Logic
    if "study" in purpose_lower:
        return {
            "is_eu": False,
            "permit_name": "Long-term Visa for the Purpose of Study (D/VR/24)",
            "description": "Recommended for university students. Must be applied for at a Czech embassy outside of the Czech Republic.",
            "processing_time": "60 days (usually fast-tracked for accredited universities)",
            "next_steps": "Gather study confirmation, accommodation proof, funds proof, and apply at the nearest Czech embassy/consulate."
        }
    elif "work" in purpose_lower:
        return {
            "is_eu": False,
            "permit_name": "Employee Card (Zaměstnanecká karta)",
            "description": "A dual permit combining both residence permit and work permit. Tied to a specific job registered in the central vacancy database.",
            "processing_time": "60-90 days",
            "next_steps": "1. Secure a job offer from an employer willing to sponsor. 2. Employer registers vacancy with Labor Office. 3. Apply for Employee Card at Czech embassy."
        }
    elif "business" in purpose_lower or "nomad" in purpose_lower:
        return {
            "is_eu": False,
            "permit_name": "Long-term Visa for the Purpose of Business (Živnostenský list / ZP)",
            "description": "Also known as the 'Živno' visa. Suitable for freelancers, independent contractors, and digital nomads who register a trade license.",
            "processing_time": "90-120 days",
            "next_steps": "1. Obtain a Czech trade license (Živnostenský list) with Prague trade office. 2. Get proof of accommodation and business funds. 3. Attend visa interview at Czech embassy."
        }
    else:
        return {
            "is_eu": False,
            "permit_name": "Long-term Visa / Residence Permit (General)",
            "description": "Please consult the Ministry of Interior guidance. If relocating for family reunification, apply for a Long-term Residence Permit for the Purpose of Family Reunification.",
            "processing_time": "90-120 days",
            "next_steps": "Identify embassy, gather civil documents (birth/marriage certificates translated to Czech), and book appointment."
        }

@mcp.tool()
def get_required_documents(permit_type: str) -> dict:
    """Get the checklist of required documents for a specific visa or residence permit.

    Args:
        permit_type: Name of the permit (e.g. Employee Card, Student Visa, Business Visa).
    """
    logger.info(f"get_required_documents called for permit_type={permit_type}")
    pt = permit_type.lower()
    
    base_docs = [
        "Valid passport (must not be older than 10 years and must be valid 3 months beyond visa validity)",
        "Completed visa application form",
        "2 passport-sized photographs (3.5 x 4.5 cm)",
        "Proof of accommodation in Prague (lease agreement or proof of accommodation signed by owner with notarized signature)",
    ]

    if "student" in pt or "study" in pt:
        specifics = [
            "Confirmation of studies (Potvrzení o studiu) from a Czech school/university (in Czech)",
            "Proof of sufficient financial resources (bank statement + active debit card on your name, min ~ Czech Crown 110,000 / €4,500 per year)",
            "Criminal record check (police clearance certificate) from home country (officially translated into Czech)",
            "Comprehensive travel health insurance (must be purchased from pVZP for non-EU students for stays over 90 days)"
        ]
    elif "employee" in pt or "work" in pt:
        specifics = [
            "Employment contract or agreement on work activity (signed by both parties, with salary above minimum wage)",
            "Documents proving professional qualification (diploma, certificates, officially translated and authenticated if needed)",
            "Criminal record check from home country and any country resided in for >6 months in last 3 years",
            "Travel medical insurance (for entry period, once employed you join the public system)"
        ]
    elif "business" in pt or "živno" in pt or "nomad" in pt:
        specifics = [
            "Czech Trade License (Živnostenský list) or confirmation from Trade Register",
            "Proof of financial resources (bank statement showing min ~ Czech Crown 200,000 / €8,000)",
            "Criminal record check from home country (officially translated into Czech)",
            "Confirmation of no tax debts from Czech Social Security (ČSSZ) and Financial Office (if already registered)",
            "Comprehensive travel health insurance (pVZP is the exclusive provider for long-term visa applicants)"
        ]
    else:
        specifics = [
            "Proof of purpose of stay (marriage certificate, birth certificate, or other official proof, translated to Czech)",
            "Proof of funds matching the legal minimum based on Czech subsistence minimum",
            "Criminal record check",
            "Comprehensive travel health insurance"
        ]

    return {
        "permit_type": permit_type,
        "required_documents": base_docs + specifics,
        "translation_rule": "IMPORTANT: All documents not in Czech must be officially translated into the Czech language by a certified court translator. Foreign public documents (e.g., diplomas, police certificates) may require an Apostille or Superlegalization."
    }

@mcp.tool()
def get_office_locations(office_type: str) -> dict:
    """Get Prague government office locations and contact details.

    Args:
        office_type: Type of office ('immigration', 'police', 'trade').
    """
    logger.info(f"get_office_locations called for office_type={office_type}")
    ot = office_type.lower()
    
    if "immigration" in ot or "mvcr" in ot:
        return {
            "office_name": "Ministry of the Interior - Department for Asylum and Migration Policy (OAMP MVČR)",
            "locations": [
                {
                    "name": "OAMP Prague III (Letná)",
                    "address": "Nad Štolou 936/3, Prague 7",
                    "districts_served": "Prague 1, 3, 6, 7, 8, 9",
                    "services": "Schengen visas, long-term visas, residence permits for students and employees",
                    "booking": "Highly recommended to book online via the MVCR portal or phone +420 974 801 801."
                },
                {
                    "name": "OAMP Prague II (Cigánkova)",
                    "address": "Cigánkova 1861/2, Prague 4 - Chodov",
                    "districts_served": "Prague 2, 4, 5, 10",
                    "services": "Biometrics, residence permits, long-term visas",
                    "booking": "Online portal or phone booking."
                }
            ]
        }
    elif "police" in ot or "foreign" in ot:
        return {
            "office_name": "Foreign Police (Cizinecká policie)",
            "locations": [
                {
                    "name": "Prague Foreign Police Department",
                    "address": "Olšanská 2176/2, Prague 3",
                    "services": "Address registration within 30 days of arrival (for EU citizens) or 3 working days (for non-EU citizens), reporting changes, requesting travel validation",
                    "hours": "Mon/Wed: 8:00 - 17:00, Tue/Thu: 8:00 - 14:00"
                }
            ]
        }
    elif "trade" in ot or "živnost" in ot:
        return {
            "office_name": "Municipal Trade License Office (Živnostenský úřad)",
            "locations": [
                {
                    "name": "Prague 1 Trade Office",
                    "address": "Vodičkova 681/18, Prague 1",
                    "services": "Registration of trade licenses (Živnostenský list) for freelancers and entrepreneurs, issuing trade register extracts",
                    "requirements": "Bring passport, criminal record check, proof of accommodation, and fee of 1,000 CZK."
                }
            ]
        }
    else:
        return {
            "error": "Office type not found. Use 'immigration' (MVCR), 'police' (Foreign Police), or 'trade' (Živnostenský úřad)."
        }

@mcp.tool()
def get_health_insurance_info(duration_months: int) -> dict:
    """Get legal Czech health insurance requirements for foreigners based on duration of stay.

    Args:
        duration_months: Planned duration of stay in months.
    """
    logger.info(f"get_health_insurance_info called for duration_months={duration_months}")
    
    if duration_months <= 3:
        return {
            "insurance_type": "Travel Medical Insurance (Basic/Emergency)",
            "coverage_requirement": "Minimum coverage limit of EUR 30,000 including repatriation of remains. Must not exclude emergency care.",
            "notes": "Schengen travel insurance is sufficient for short-term stays under 90 days. EU citizens can use EHIC (European Health Insurance Card) for emergency care."
        }
    else:
        return {
            "insurance_type": "Comprehensive Health Insurance (Komplexní zdravotní pojištění)",
            "coverage_requirement": "Minimum coverage limit of EUR 60,000 per insurance event. Must cover preventive care, pregnancy, and childbirth.",
            "exclusive_provider": "pVZP (Pojišťovna VZP) was previously the exclusive provider for long-term visa holders. Since September 2023, the monopoly was lifted, and you can buy from other commercial insurers (like Maxima, Slavia, Ergo) provided it meets the comprehensive requirements.",
            "exceptions": "Foreigners employed by a Czech company with a standard employment contract automatically enter the Czech public health insurance system (VZP, OZP, Vojenská, etc.) from day one. In this case, private comprehensive insurance is not required."
        }

if __name__ == "__main__":
    mcp.run()

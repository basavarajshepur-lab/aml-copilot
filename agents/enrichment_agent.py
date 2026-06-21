"""
Enrichment Agent — entity due diligence via tool use.

Takes a raw AML alert and enriches it with:
- Sanctions screening (OFAC, UN, EU, HMT)
- PEP (Politically Exposed Person) status
- Adverse media
- Country risk rating

In production: these tools connect to real screening APIs (Worldcheck, Refinitiv,
ComplyAdvantage). In this demo: realistic mock responses based on entity/country
characteristics, so the full pipeline logic is demonstrable without paid API keys.

Design decision: separate enrichment from risk analysis so each agent has a
single responsibility and can be swapped independently. Enrichment uses tool use;
risk analysis uses reasoning over structured enrichment output.
"""

import json
import re
from anthropic import Anthropic
from core.models import Alert, EnrichedAlert, SanctionsHit, CountryRisk

client = Anthropic()

# --- Mock screening tools (replace with real API calls in production) ---

SANCTIONED_ENTITIES = {
    "north korea": True, "iran": True, "russia": True, "syria": True,
    "myanmar": True, "belarus": True, "cuba": True, "venezuela": True,
}

COUNTRY_RISK_MAP = {
    "US": CountryRisk.LOW, "GB": CountryRisk.LOW, "DE": CountryRisk.LOW,
    "FR": CountryRisk.LOW, "SG": CountryRisk.LOW, "JP": CountryRisk.LOW,
    "AE": CountryRisk.MEDIUM, "CN": CountryRisk.MEDIUM, "IN": CountryRisk.MEDIUM,
    "BR": CountryRisk.MEDIUM, "MX": CountryRisk.MEDIUM, "TR": CountryRisk.MEDIUM,
    "NG": CountryRisk.HIGH, "KE": CountryRisk.HIGH, "PK": CountryRisk.HIGH,
    "AF": CountryRisk.VERY_HIGH, "KP": CountryRisk.VERY_HIGH, "IR": CountryRisk.VERY_HIGH,
    "SY": CountryRisk.VERY_HIGH, "MM": CountryRisk.VERY_HIGH,
}


def search_sanctions_list(entity_name: str, list_name: str = "ALL") -> dict:
    """Screen entity against sanctions lists. Mock implementation."""
    name_lower = entity_name.lower()
    hits = []
    for sanctioned, _ in SANCTIONED_ENTITIES.items():
        if sanctioned in name_lower:
            hits.append({
                "list": "OFAC SDN",
                "match_type": "partial",
                "match_score": 0.85,
                "details": f"Name contains reference to sanctioned jurisdiction: {sanctioned}"
            })
    # Simulate a known bad actor
    if "kowalski trading" in name_lower or "atlas global" in name_lower:
        hits.append({
            "list": "EU Consolidated List",
            "match_type": "exact",
            "match_score": 0.99,
            "details": "Entity listed for sanctions evasion, 2023"
        })
    return {"hits": hits, "screened_lists": ["OFAC SDN", "EU Consolidated", "UN", "HMT"]}


def check_pep_status(entity_name: str, country: str) -> dict:
    """Check if entity is a Politically Exposed Person. Mock implementation."""
    pep_keywords = ["minister", "senator", "president", "governor", "ambassador",
                    "general", "colonel", "director-general"]
    name_lower = entity_name.lower()
    is_pep = any(kw in name_lower for kw in pep_keywords)
    # Simulate known PEP
    if "ibrahim al-" in name_lower or "chen wei" in name_lower:
        is_pep = True
    return {
        "is_pep": is_pep,
        "pep_category": "Government Official" if is_pep else None,
        "pep_country": country if is_pep else None,
        "source": "PEP database (mock)"
    }


def search_adverse_media(entity_name: str) -> dict:
    """Search for negative news about entity. Mock implementation."""
    findings = []
    name_lower = entity_name.lower()
    if "atlas" in name_lower:
        findings.append("Reuters 2024: Atlas group under investigation for trade-based money laundering")
    if "kowalski" in name_lower:
        findings.append("FT 2023: Kowalski Trading linked to shell company network in BVI")
    return {"findings": findings, "sources_searched": ["Reuters", "BBC", "FT", "Bloomberg"]}


def get_country_risk_rating(country_code: str) -> dict:
    """Return FATF-aligned country risk rating. Mock implementation."""
    risk = COUNTRY_RISK_MAP.get(country_code.upper(), CountryRisk.MEDIUM)
    fatf_listed = country_code.upper() in {"KP", "IR", "MM", "SY"}
    return {
        "country_code": country_code,
        "risk_rating": risk.value,
        "fatf_listed": fatf_listed,
        "basel_aml_index": "High" if risk in [CountryRisk.HIGH, CountryRisk.VERY_HIGH] else "Medium/Low",
    }


# --- Tool definitions for Claude ---

TOOLS = [
    {
        "name": "search_sanctions_list",
        "description": "Screen an entity name against OFAC, UN, EU, and HMT sanctions lists",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Full name of the entity to screen"},
                "list_name": {"type": "string", "description": "Specific list or ALL", "default": "ALL"}
            },
            "required": ["entity_name"]
        }
    },
    {
        "name": "check_pep_status",
        "description": "Check if an individual is a Politically Exposed Person",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string"},
                "country": {"type": "string", "description": "ISO 2-letter country code"}
            },
            "required": ["entity_name", "country"]
        }
    },
    {
        "name": "search_adverse_media",
        "description": "Search news and media for negative coverage of an entity",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string"}
            },
            "required": ["entity_name"]
        }
    },
    {
        "name": "get_country_risk_rating",
        "description": "Get FATF-aligned AML risk rating for a country",
        "input_schema": {
            "type": "object",
            "properties": {
                "country_code": {"type": "string", "description": "ISO 2-letter country code"}
            },
            "required": ["country_code"]
        }
    },
]

TOOL_MAP = {
    "search_sanctions_list": search_sanctions_list,
    "check_pep_status": check_pep_status,
    "search_adverse_media": search_adverse_media,
    "get_country_risk_rating": get_country_risk_rating,
}


def run(alert: Alert) -> EnrichedAlert:
    """
    Run enrichment agent: screen the alert's customer and counterparty,
    retrieve country risk, check adverse media. Returns EnrichedAlert.
    """
    system = """You are an AML enrichment specialist at a tier-1 bank.
Your job is to use the available tools to gather due diligence information
about the customer and counterparty in an AML alert.
Screen both the customer name and counterparty name. Always check country risk.
Be thorough — missing a sanctions hit is worse than a false positive at this stage."""

    user_message = f"""Please enrich this AML alert with due diligence information:

Alert ID: {alert.alert_id}
Customer: {alert.customer_name}
Counterparty: {alert.counterparty_name}
Counterparty Country: {alert.counterparty_country}
Transaction: {alert.amount} {alert.currency} via {alert.transaction_type}
Rule triggered: {alert.rule_triggered}
Risk indicators: {', '.join(alert.risk_indicators)}

Use the available tools to:
1. Screen customer name against sanctions lists
2. Screen counterparty name against sanctions lists
3. Check if counterparty is a PEP
4. Search for adverse media on counterparty
5. Get country risk rating for counterparty country

Then provide a JSON summary of your findings with keys:
sanctions_hits, is_pep, pep_details, adverse_media_findings,
counterparty_country_risk, enrichment_confidence (0-1), enrichment_notes"""

    messages = [{"role": "user", "content": user_message}]
    sanctions_hits = []
    is_pep = False
    pep_details = None
    adverse_media = []
    country_risk = CountryRisk.MEDIUM

    # Agentic loop: let Claude call tools until it has enough information
    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_fn = TOOL_MAP.get(block.name)
                    result = tool_fn(**block.input) if tool_fn else {"error": "unknown tool"}

                    # Collect results as we go
                    if block.name == "search_sanctions_list" and result.get("hits"):
                        for hit in result["hits"]:
                            sanctions_hits.append(SanctionsHit(
                                list_name=hit["list"],
                                match_type=hit["match_type"],
                                match_score=hit["match_score"],
                                entity_details=hit["details"],
                            ))
                    elif block.name == "check_pep_status":
                        is_pep = result.get("is_pep", False)
                        pep_details = result.get("pep_category") if is_pep else None
                    elif block.name == "search_adverse_media":
                        adverse_media.extend(result.get("findings", []))
                    elif block.name == "get_country_risk_rating":
                        risk_str = result.get("risk_rating", "MEDIUM")
                        country_risk = CountryRisk(risk_str)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # Extract confidence from final response
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            confidence = 0.8
            conf_match = re.search(r"enrichment_confidence[\"']?\s*:\s*([0-9.]+)", final_text)
            if conf_match:
                confidence = float(conf_match.group(1))

            break

    return EnrichedAlert(
        original_alert=alert,
        sanctions_hits=sanctions_hits,
        is_pep=is_pep,
        pep_details=pep_details,
        adverse_media_findings=adverse_media,
        counterparty_country_risk=country_risk,
        enrichment_confidence=confidence,
        enrichment_notes=f"Screened via multi-tool enrichment pipeline. {len(sanctions_hits)} sanctions hits.",
    )

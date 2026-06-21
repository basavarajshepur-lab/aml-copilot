"""
Risk Analysis Agent — AML alert triage via structured reasoning.

Takes enriched alert data and produces a triage decision with:
- Risk score (0-100)
- Decision: DISMISS / MONITOR / ESCALATE / SAR
- Confidence score
- Explicit reasoning chain (required for audit trail)
- Key red flags and mitigating factors

Design decision: low temperature (0.1) for consistency. AML decisions must be
reproducible — the same alert should produce the same decision. We use structured
output via tool use to guarantee parseable, auditable output every time.

Confidence threshold drives HITL routing: below HITL_THRESHOLD, decision goes
to analyst queue regardless of the AI recommendation.
"""

import os
import json
from anthropic import Anthropic
from core.models import EnrichedAlert, TriageDecision, RiskDecision

client = Anthropic()

HITL_THRESHOLD = float(os.getenv("HITL_THRESHOLD", "0.85"))

SYSTEM_PROMPT = """You are a senior AML analyst at a tier-1 global bank with 15 years of experience.
You specialise in reviewing transaction monitoring alerts and making triage decisions.

Your decisions carry regulatory weight. Every conclusion must be:
1. Evidence-based — cite specific facts from the alert and enrichment data
2. Proportionate — don't over-escalate; unnecessary SARs waste regulator capacity
3. Documented — your reasoning will be reviewed by the MLRO and potentially by the FCA

AML typologies you are expert in:
- Structuring (smurfing): transactions just below reporting thresholds
- Layering: rapid movement through multiple accounts to obscure origin
- Integration: legitimate-looking transactions after layering
- Trade-based ML: over/under-invoicing, multiple invoicing
- PEP risk: enhanced due diligence required for all PEPs
- Sanctions evasion: shell companies, front companies, indirect routing"""


def _build_analysis_tool() -> dict:
    """Structured output schema for triage decision."""
    return {
        "name": "record_triage_decision",
        "description": "Record the structured AML triage decision for audit trail",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "0=clearly legitimate, 100=certain SAR filing required"
                },
                "decision": {
                    "type": "string",
                    "enum": ["DISMISS", "MONITOR", "ESCALATE", "SAR"],
                    "description": "DISMISS=no action, MONITOR=watch account, ESCALATE=senior review, SAR=file report"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence in the decision. Below 0.85 triggers mandatory human review."
                },
                "reasoning": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Factors considered, in descending order of weight. Be specific."
                },
                "key_red_flags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific suspicious indicators identified"
                },
                "mitigating_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Factors that reduce the concern level"
                },
                "recommended_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific next steps for the compliance team"
                },
                "typology_match": {
                    "type": "string",
                    "description": "Primary AML typology this alert matches, if any"
                }
            },
            "required": ["risk_score", "decision", "confidence", "reasoning",
                        "key_red_flags", "mitigating_factors", "recommended_actions"]
        }
    }


def run(enriched_alert: EnrichedAlert) -> TriageDecision:
    """
    Analyse enriched alert and produce structured triage decision.
    Returns TriageDecision with routing instruction for HITL queue.
    """
    alert = enriched_alert.original_alert

    sanctions_summary = (
        f"{len(enriched_alert.sanctions_hits)} sanctions hits: "
        + "; ".join([f"{h.list_name} ({h.match_type}, score {h.match_score:.2f})"
                     for h in enriched_alert.sanctions_hits])
        if enriched_alert.sanctions_hits else "No sanctions hits"
    )

    user_message = f"""Review this AML alert and provide your triage decision.

=== ALERT DETAILS ===
Alert ID: {alert.alert_id}
Customer: {alert.customer_name} (Account type: {alert.account_type})
Transaction: {alert.amount:,.2f} {alert.currency}
Type: {alert.transaction_type}
Counterparty: {alert.counterparty_name} at {alert.counterparty_bank} ({alert.counterparty_country})
Rule triggered: {alert.rule_triggered}
Account history: {alert.account_history_summary}
Risk indicators: {', '.join(alert.risk_indicators)}

=== ENRICHMENT RESULTS ===
Sanctions screening: {sanctions_summary}
PEP status: {'YES — ' + enriched_alert.pep_details if enriched_alert.is_pep else 'No PEP match'}
Adverse media: {'; '.join(enriched_alert.adverse_media_findings) if enriched_alert.adverse_media_findings else 'None found'}
Counterparty country risk: {enriched_alert.counterparty_country_risk.value}
Enrichment confidence: {enriched_alert.enrichment_confidence:.0%}

Use the record_triage_decision tool to provide your structured assessment."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        temperature=0.1,
        system=SYSTEM_PROMPT,
        tools=[_build_analysis_tool()],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "record_triage_decision":
            data = block.input
            return TriageDecision(
                risk_score=data["risk_score"],
                decision=RiskDecision(data["decision"]),
                confidence=data["confidence"],
                reasoning=data["reasoning"],
                key_red_flags=data["key_red_flags"],
                mitigating_factors=data["mitigating_factors"],
                recommended_actions=data["recommended_actions"],
                typology_match=data.get("typology_match"),
            )

    # Fallback: if structured output not returned, default to ESCALATE for safety
    return TriageDecision(
        risk_score=50,
        decision=RiskDecision.ESCALATE,
        confidence=0.3,
        reasoning=["Structured analysis could not be completed — escalating for safety"],
        key_red_flags=["Analysis error"],
        mitigating_factors=[],
        recommended_actions=["Manual review required"],
    )

"""
SAR Narrative Agent — drafts Suspicious Activity Report narratives.

Only invoked when triage decision is SAR. Produces a structured narrative
in FCA (UK) / FinCEN (US) format that an MLRO can review and file.

Design decision: this agent is last in the pipeline and never runs automatically.
The HITL queue always shows SAR recommendations to an analyst before any narrative
is used. The analyst reviews both the triage decision AND the narrative draft.

In production: SAR filing goes through the bank's FCA/FinCEN reporting system
(UKFIU SARs Online, FinCEN BSA E-Filing). This agent produces the draft only.
"""

from anthropic import Anthropic
from core.models import EnrichedAlert, TriageDecision, SARNarrative

client = Anthropic()

SYSTEM_PROMPT = """You are an experienced MLRO (Money Laundering Reporting Officer) drafting
a Suspicious Activity Report. Your narrative must be:

1. Factual — based only on information in the alert and enrichment data
2. Clear — written for a financial intelligence unit analyst who is not familiar with this customer
3. Complete — covering who, what, when, where, why suspicious
4. Proportionate — do not overstate certainty; use "may indicate" not "proves"
5. Compliant — follow FCA guidance on SAR content (NCA guidance note 2023)

Do NOT include: speculation, personal opinions, information not in the alert data,
customer racial/ethnic profiling, or protected characteristics."""


def run(
    enriched_alert: EnrichedAlert,
    triage_decision: TriageDecision,
) -> SARNarrative:
    """Draft SAR narrative for MLRO review. Never filed automatically."""
    alert = enriched_alert.original_alert

    user_message = f"""Draft a SAR narrative for the following alert.

ALERT: {alert.alert_id}
Customer: {alert.customer_name}, Account: {alert.account_type}
Transaction: {alert.amount:,.2f} {alert.currency} to {alert.counterparty_name} ({alert.counterparty_country})
Transaction type: {alert.transaction_type}
Date/time: {alert.timestamp}
Rule triggered: {alert.rule_triggered}
Account history: {alert.account_history_summary}

ENRICHMENT:
Sanctions hits: {[h.model_dump() for h in enriched_alert.sanctions_hits]}
PEP: {enriched_alert.is_pep} — {enriched_alert.pep_details}
Adverse media: {enriched_alert.adverse_media_findings}
Country risk: {enriched_alert.counterparty_country_risk.value}

ANALYST TRIAGE:
Risk score: {triage_decision.risk_score}/100
Key red flags: {triage_decision.key_red_flags}
Typology: {triage_decision.typology_match}

Produce a SAR narrative with these sections:
1. subject_information: Who the subject is and their relationship to the bank
2. transaction_details: Factual description of the transaction(s)
3. suspicious_activity_description: What activity is suspicious and why
4. why_suspicious: The specific reasons this meets the SAR threshold
5. supporting_evidence: List of specific evidence items
6. recommended_filing_jurisdiction: FCA/NCA (UK) or FinCEN (US) or both

Write in clear, professional language. This draft will be reviewed by the MLRO before any filing."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Parse structured sections from response
    text = response.content[0].text

    def extract_section(text: str, section: str) -> str:
        import re
        pattern = rf"{re.escape(section)}[:\s]*(.+?)(?=\n[A-Z][a-z_]+:|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return SARNarrative(
        subject_information=extract_section(text, "subject_information") or text[:300],
        transaction_details=extract_section(text, "transaction_details") or "",
        suspicious_activity_description=extract_section(text, "suspicious_activity_description") or "",
        why_suspicious=extract_section(text, "why_suspicious") or "",
        supporting_evidence=[flag for flag in triage_decision.key_red_flags],
        recommended_filing_jurisdiction=extract_section(text, "recommended_filing_jurisdiction") or "FCA/NCA (UK)",
    )

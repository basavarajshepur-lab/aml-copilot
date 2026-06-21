"""
AML Copilot Pipeline — orchestrates the full multi-agent triage workflow.

Flow:
  Alert → Enrichment Agent → Risk Analysis Agent → [SAR?] Narrative Agent
       → HITL Queue (if confidence < threshold) → Audit Trail → Result

Design decisions:
- Enrichment always runs first; risk analysis never sees raw alert without context
- Narrative agent only runs for SAR decisions (cost control + proportionality)
- Every result is logged to audit trail before being returned
- Low-confidence decisions always go to HITL regardless of the decision itself
"""

import os
import time
import uuid
from agents import enrichment_agent, risk_analysis_agent, narrative_agent
from core.models import Alert, PipelineResult, RiskDecision
from core.audit_trail import log_ai_decision

HITL_THRESHOLD = float(os.getenv("HITL_THRESHOLD", "0.85"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))


def process_alert(alert: Alert) -> PipelineResult:
    """
    Run a single alert through the full AML triage pipeline.
    Returns PipelineResult with triage decision, optional SAR draft, and audit ID.
    """
    start_ms = time.time() * 1000

    # Stage 1: Entity enrichment via tool use
    enriched = enrichment_agent.run(alert)

    # Stage 2: Risk analysis with structured reasoning
    decision = risk_analysis_agent.run(enriched)

    # Stage 3: SAR narrative (only if SAR decision)
    sar_narrative = None
    if decision.decision == RiskDecision.SAR:
        sar_narrative = narrative_agent.run(enriched, decision)

    # Stage 4: Log to audit trail (always, before returning)
    audit_id = log_ai_decision(alert.alert_id, enriched, decision)

    # Stage 5: Determine if HITL review is needed
    # HITL triggered if: confidence below threshold OR decision is SAR/ESCALATE
    requires_hitl = (
        decision.confidence < HITL_THRESHOLD
        or decision.decision in [RiskDecision.SAR, RiskDecision.ESCALATE]
    )

    elapsed_ms = (time.time() * 1000) - start_ms

    return PipelineResult(
        alert_id=alert.alert_id,
        enriched_alert=enriched,
        triage_decision=decision,
        sar_narrative=sar_narrative,
        sent_to_hitl=requires_hitl,
        audit_id=audit_id,
        processing_time_ms=round(elapsed_ms, 1),
    )

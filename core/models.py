"""
Pydantic models for the AML Copilot pipeline.
Every field is typed and documented — audit trail integrity depends on this.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AlertType(str, Enum):
    STRUCTURING = "structuring"
    LAYERING = "layering"
    WIRE_TRANSFER = "wire_transfer"
    CASH_INTENSIVE = "cash_intensive"
    PEP_TRANSACTION = "pep_transaction"
    RAPID_MOVEMENT = "rapid_movement"
    CRYPTO = "crypto"
    TRADE_FINANCE = "trade_finance"
    UNUSUAL_PATTERN = "unusual_pattern"


class RiskDecision(str, Enum):
    DISMISS = "DISMISS"
    MONITOR = "MONITOR"
    ESCALATE = "ESCALATE"
    SAR = "SAR"  # Suspicious Activity Report


class CountryRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class Alert(BaseModel):
    alert_id: str
    timestamp: str
    customer_id: str
    customer_name: str
    account_type: str
    transaction_type: str
    amount: float
    currency: str
    counterparty_name: str
    counterparty_country: str
    counterparty_bank: str
    alert_type: AlertType
    rule_triggered: str
    account_history_summary: str
    risk_indicators: list[str]


class SanctionsHit(BaseModel):
    list_name: str  # OFAC, UN, EU, HMT
    match_type: str  # exact, fuzzy, alias
    match_score: float  # 0-1
    entity_details: str


class EnrichedAlert(BaseModel):
    original_alert: Alert
    sanctions_hits: list[SanctionsHit] = Field(default_factory=list)
    is_pep: bool = False
    pep_details: Optional[str] = None
    adverse_media_findings: list[str] = Field(default_factory=list)
    counterparty_country_risk: CountryRisk = CountryRisk.LOW
    beneficial_owner_flags: list[str] = Field(default_factory=list)
    enrichment_confidence: float = Field(ge=0.0, le=1.0)
    enrichment_notes: str = ""


class TriageDecision(BaseModel):
    risk_score: int = Field(ge=0, le=100, description="0=clean, 100=certain SAR")
    decision: RiskDecision
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: list[str] = Field(description="Factors considered, in order of weight")
    key_red_flags: list[str]
    mitigating_factors: list[str]
    recommended_actions: list[str]
    typology_match: Optional[str] = None


class SARNarrative(BaseModel):
    subject_information: str
    transaction_details: str
    suspicious_activity_description: str
    why_suspicious: str
    supporting_evidence: list[str]
    recommended_filing_jurisdiction: str


class HITLQueueItem(BaseModel):
    queue_id: str
    alert_id: str
    enriched_alert: EnrichedAlert
    triage_decision: TriageDecision
    sar_narrative: Optional[SARNarrative] = None
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    requires_hitl: bool = True
    priority: str = "NORMAL"  # NORMAL, HIGH, URGENT


class AuditEntry(BaseModel):
    audit_id: str
    alert_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: str  # enrichment, triage, hitl_review, final
    ai_decision: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    analyst_id: Optional[str] = None
    analyst_decision: Optional[str] = None
    analyst_notes: Optional[str] = None
    final_outcome: Optional[str] = None


class PipelineResult(BaseModel):
    alert_id: str
    enriched_alert: EnrichedAlert
    triage_decision: TriageDecision
    sar_narrative: Optional[SARNarrative] = None
    sent_to_hitl: bool
    audit_id: str
    processing_time_ms: float

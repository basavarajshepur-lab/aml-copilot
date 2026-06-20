# Product Requirements Document
## AML Copilot — Multi-Agent Alert Triage System

**Version:** 1.0  
**Author:** Basavaraj Shepur  
**Status:** Production-Ready Demo

---

## Problem Statement

Global banks spend £25–35 billion per year on AML compliance. The largest cost driver is not technology — it is the manual review of transaction monitoring alerts. Industry data consistently shows that 95–99% of AML alerts are false positives. At a typical tier-1 bank, 800–1,200 compliance analysts spend the majority of their working day dismissing legitimate transactions that triggered automated rules.

The current state:
- Rule-based transaction monitoring systems optimised for recall (catching crime) generate enormous noise
- Analysts review each alert manually: research the customer, screen the counterparty, assess risk, document decision
- Average alert review time: 20–45 minutes per alert
- Opportunity cost: analysts who should be investigating genuine suspicious activity are buried in false positives
- Regulatory pressure: FCA and FinCEN require documented rationale for every dismissed alert

The result: high cost, low analyst morale, and — paradoxically — worse AML outcomes because analysts experiencing alert fatigue miss signals buried in noise.

---

## User Personas

**1. AML Analyst (primary user)**
- Reviews 20–60 alerts per day
- Needs: fast enrichment data, clear AI recommendation, easy override workflow, audit trail
- Pain: repetitive false-positive dismissal, context-switching between 6+ systems per alert

**2. Compliance Manager / MLRO**
- Oversees alert queue, responsible for SAR filing decisions
- Needs: dashboard visibility, quality metrics, escalation workflow, regulatory reporting
- Pain: no visibility into AI recommendation quality, manual SAR drafting

**3. Model Risk / Audit**
- Reviews AI decision quality, regulatory audit readiness
- Needs: full audit trail, explainability, override rate tracking
- Pain: black-box AI decisions with no documented rationale

---

## User Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-01 | AML Analyst | See AI triage recommendation with reasoning before I review | I can focus attention on alerts where I add value |
| US-02 | AML Analyst | See enrichment data (sanctions, PEP, adverse media) pre-populated | I don't have to query 4 systems manually per alert |
| US-03 | AML Analyst | Override AI recommendation with a documented reason | I remain in control; AI is advisory not decisional |
| US-04 | MLRO | See a draft SAR narrative when AI recommends SAR | I can review and file faster, with less drafting from scratch |
| US-05 | MLRO | See dashboard of queue stats and escalation rate | I understand throughput and AI performance at a glance |
| US-06 | Audit | Export full audit trail including AI recommendation and analyst decision | I can demonstrate to FCA/FinCEN that every decision was documented |
| US-07 | Analyst | Process a batch of alerts from a CSV upload | I can work through a backlog efficiently |

---

## Functional Requirements

### FR-01: Multi-Agent Pipeline
- System must run three sequential agents: Enrichment → Risk Analysis → Narrative (SAR only)
- Enrichment agent must screen customer and counterparty against sanctions lists, PEP database, adverse media
- Risk analysis agent must produce structured decision: score (0-100), decision (DISMISS/MONITOR/ESCALATE/SAR), confidence (0-1), reasoning chain
- Narrative agent must only run when decision is SAR

### FR-02: HITL Routing
- Any decision with confidence < 0.85 must be routed to analyst review queue
- SAR and ESCALATE decisions must always route to analyst review regardless of confidence
- Analyst must be able to agree with AI or override to any other decision
- Override must require a text note (not optional)

### FR-03: Audit Trail
- Every AI decision must be logged before being presented to analyst
- Log must include: alert_id, timestamp, ai_decision, ai_confidence, ai_reasoning (full JSON)
- Analyst review must be logged against the same audit_id: analyst_id, analyst_decision, notes, final_outcome
- Audit trail must be exportable to CSV for regulatory submission
- Audit trail must be append-only (no deletes)

### FR-04: Explainability
- Every triage decision must include: key red flags, mitigating factors, numbered reasoning chain
- Reasoning must reference specific alert data, not generic statements

### FR-05: Batch Processing
- System must accept JSON file of alerts and process all sequentially
- Batch results must be downloadable as CSV

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Processing time per alert | < 30 seconds end-to-end |
| Audit trail retention | Indefinite (regulatory requirement) |
| Explainability | Every decision must have documented reasoning |
| Override capability | Analyst must always be able to override AI |
| Availability | Demo: local. Production: 99.9% uptime |

---

## Out of Scope (v1.0)

- Direct integration with production TMS (NICE Actimize, Tonbeller, FCRM)
- Real-time screening API integration (Worldcheck, ComplyAdvantage) — mocked in demo
- SAR filing API integration (UKFIU SARs Online, FinCEN BSA E-Filing)
- Customer risk rating model
- Multi-tenancy / user authentication
- Case management workflow

---

## Success Metrics

| Metric | Baseline | Target |
|---|---|---|
| Alert review time (analyst) | 20–45 min/alert | < 10 min/alert with AI pre-work |
| False positive auto-dismiss rate | 0% (all manual) | 60–70% auto-dismissed at high confidence |
| SAR drafting time | 60–90 min | < 20 min with AI narrative draft |
| Audit trail completeness | Inconsistent | 100% of decisions logged |
| Analyst override rate | N/A | Target < 15% (validates AI quality) |

---

## Responsible AI Considerations

See `docs/responsible-ai-checklist.md` for full governance framework.

Key principles applied in this system:
1. **AI is advisory, not decisional** — analyst always has final say
2. **Transparency by default** — every recommendation includes full reasoning
3. **Conservative routing** — doubt triggers human review, not auto-dismiss
4. **Audit trail integrity** — AI recommendations logged before analyst sees them (prevents post-hoc rationalisation)
5. **No protected characteristics** — enrichment data limited to financial and regulatory facts

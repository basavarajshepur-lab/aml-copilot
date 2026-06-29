# AML Copilot

**Multi-agent AML alert triage system** — enrichment, risk scoring, SAR drafting, HITL queue, and audit trail for financial crime compliance.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Status](https://img.shields.io/badge/Status-Production--Ready%20Demo-brightgreen) ![Claude](https://img.shields.io/badge/Powered%20by-Claude%20AI-orange)

---

## The Problem

Global banks spend **£25–35 billion per year** on AML compliance. The largest cost driver is not technology — it is people manually reviewing alerts that automated systems flag.

**95–99% of AML transaction monitoring alerts are false positives.**

At a typical tier-1 bank, 800–1,200 compliance analysts spend their working day dismissing legitimate transactions. Average review time: 20–45 minutes per alert. The analysts who should be investigating genuine financial crime are buried in noise.

The problem isn't catching criminals. It's the cost of not catching them faster.

---

## What AML Copilot Does

A three-agent pipeline that triages an AML alert from raw data to documented decision in under 30 seconds:

```
                    ┌─────────────────────────────────────────────────────┐
                    │                  AML COPILOT PIPELINE               │
                    └─────────────────────────────────────────────────────┘

  Raw Alert                Enrichment Agent           Risk Analysis Agent
┌──────────┐   ─────►   ┌─────────────────┐   ─►   ┌──────────────────┐
│ Customer │             │ • Sanctions scan │         │ • Risk score 0-100│
│ Amount   │             │ • PEP check      │         │ • DISMISS/MONITOR │
│ Counterp.│             │ • Adverse media  │         │   ESCALATE/SAR   │
│ Rule     │             │ • Country risk   │         │ • Reasoning chain │
└──────────┘             └─────────────────┘         │ • Confidence 0-1  │
                                                       └──────────────────┘
                                                                │
                                   ┌────────────────────────────┤
                                   │                            │
                              [confidence                  [SAR decision]
                               < 0.85 OR                        │
                              ESCALATE/SAR]               Narrative Agent
                                   │                      ┌────────────┐
                                   ▼                      │ SAR draft  │
                            HITL Review Queue             │ FCA/FinCEN │
                           ┌───────────────┐              │ format     │
                           │ Analyst UI    │◄─────────────┘
                           │ Agree/Override│
                           └───────────────┘
                                   │
                                   ▼
                             Audit Trail (SQLite)
                          Every decision logged.
                          Append-only. Exportable.
```

---

## Features

- **Enrichment Agent** — screens customer and counterparty against sanctions lists (OFAC, UN, EU, HMT), PEP databases, and adverse media using Claude tool use
Here are the full forms of those sanctions and regulatory bodies:OFAC: Office of Foreign Assets Control (US)UN: United NationsEU: European UnionHMT: Her Majesty's Treasury (UK) Note: This is now formally known as His Majesty's Treasury following the accession of King Charles III.
- **Risk Analysis Agent** — structured reasoning at low temperature: risk score, triage decision, confidence, numbered reasoning chain, red flags, mitigating factors
- **SAR Narrative Agent** — drafts Suspicious Activity Report in FCA/FinCEN format; only runs on SAR decisions; always requires MLRO (Money Laundering Reporting Officer) review
- **HITL Queue** — decisions below 0.85 confidence, and all SAR/ESCALATE decisions, route to analyst review before any action is taken
- **Audit Trail** — append-only SQLite log: AI recommendation → analyst decision → final outcome. Exportable to CSV for regulatory submission
- **Streamlit UI** — analyst review interface with enrichment panel, reasoning display, decision workflow, and queue dashboard
- **Batch processing** — process a JSON file of alerts via CLI; download results as CSV
- **10 sample alerts** — covering structuring, layering, PEP transactions, trade finance ML, crypto, mule accounts, and legitimate-but-flagged transactions

---

## Quick Start

```bash
git clone https://github.com/basavarajshepur-lab/aml-copilot
cd aml-copilot
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
streamlit run app.py
if the above command doesn't work then execute - python -m streamlit run app.py
```

**CLI — process a single alert:**
```bash
python run_pipeline.py --alert data/sample_alerts.json --id ALERT_002
```

**CLI — batch process all sample alerts:**
```bash
python run_pipeline.py --batch data/sample_alerts.json
```

---

## Sample Output

```
Alert ID : ALERT_002
Decision : SAR  (risk score: 88/100)
Confidence: 91%  |  HITL required: True
Audit ID : 3f7a9b2c-...

Red flags:
  • 5 cash deposits totalling £47,100 in 30 days, all just below £10,000 threshold
  • No business account despite apparent cash-generating activity
  • New deposit behaviour inconsistent with 8-month account history
  • Transfers to own company with no declared business purpose

Reasoning:
  1. Sub-threshold cash structuring pattern: 5 deposits ranging £8,500-£9,800 is a
     textbook smurfing pattern designed to avoid £10,000 reporting threshold
  2. Volume inconsistent with declared profile: £47,100 in 30 days for a personal
     account with no declared business income is disproportionate
  3. Transfer to own company compounds concern: funds moving to entity with same
     surname suggests deliberate structuring across related accounts
  4. No mitigating explanation on file: no wealth source documented for this cash

⚠️  SAR narrative draft generated — MLRO review required before filing
```

---

## Why HITL Design Is the Hard Part

The model is the easy part. **Knowing when to trust it is the hard part.**

Three principles drive the HITL architecture:

**1. Confidence routing, not decision routing**  
Low-confidence DISMISS decisions go to human review just as high-risk SAR decisions do. A wrong auto-dismiss is just as costly as a wrong escalation.

**2. AI recommends, analyst decides**  
The AI recommendation is shown to the analyst before they can input their own view. This prevents post-hoc rationalisation of the AI decision. The analyst is reviewing the AI, not being led by it.

**3. Audit trail written before analyst sees the recommendation**  
This means we can measure AI quality independently of analyst agreement. If analysts consistently override a particular alert type, the AI's reasoning for that type needs improving.

---

## Design Decisions That Matter in Production

| Decision | Why |
|---|---|
| Low temperature (0.1) for risk analysis | AML decisions must be reproducible. Same alert, same decision. Inconsistency creates audit risk. |
| Separate enrichment and analysis agents | Enrichment is tool-calling (external data); analysis is reasoning (internal logic). Separating them makes each testable and replaceable. |
| SAR narrative always requires HITL | No exception. Regulators require MLRO sign-off on every SAR. An AI that auto-files SARs is a liability. |
| Confidence threshold at 0.85 | Calibrated for AML context: in financial crime, the cost of a missed SAR (potential £multimillion fine, reputational damage) exceeds the cost of unnecessary human review. |
| Mock enrichment tools | Real screening APIs (Worldcheck, ComplyAdvantage) require paid access. The mock tools are built to return realistic data so the full pipeline logic is demonstrable. Swap mock functions for real API calls in production. |

---

## Project Structure

```
aml-copilot/
├── app.py                    # Streamlit HITL review interface
├── run_pipeline.py           # CLI runner
├── agents/
│   ├── enrichment_agent.py   # Entity enrichment via Claude tool use
│   ├── risk_analysis_agent.py# Structured risk scoring
│   └── narrative_agent.py    # SAR draft generation
├── core/
│   ├── models.py             # Pydantic models (Alert, Decision, AuditEntry...)
│   ├── pipeline.py           # Multi-agent orchestration
│   └── audit_trail.py        # SQLite audit logging
├── data/
│   └── sample_alerts.json    # 10 realistic AML alerts across 6 typologies
└── docs/
    ├── PRD.md                # Product Requirements Document
    └── responsible-ai-checklist.md
```

---

## AML Typologies Covered in Sample Data

| Alert | Typology | Expected Decision |
|---|---|---|
| ALERT_001 | Wire to medium-risk jurisdiction (legitimate) | DISMISS |
| ALERT_002 | Structuring / smurfing | SAR |
| ALERT_003 | PEP-associated large transfer | ESCALATE |
| ALERT_004 | Layering — rapid fund movement | SAR |
| ALERT_005 | Crypto — first transaction, salary-inconsistent | MONITOR |
| ALERT_006 | Unusual hours cash deposit (legitimate business) | DISMISS |
| ALERT_007 | Trade-based ML — over-invoicing | SAR |
| ALERT_008 | BVI layering into UK property company | SAR |
| ALERT_009 | Money mule indicators | ESCALATE |
| ALERT_010 | Intra-group transfer (legitimate, FCA authorised firm) | DISMISS |

---

## Production Considerations

This is a production-ready **demo**. To deploy at a regulated institution:

1. Replace mock enrichment tools with real screening APIs (Worldcheck, ComplyAdvantage, LexisNexis)
2. Integrate with production TMS (NICE Actimize, Oracle FCRM, Temenos Financial Crime)
3. Connect SAR narrative output to FCA UKFIU SARs Online or FinCEN BSA E-Filing API
4. Complete model risk management validation under SR 11-7 (US) / SS1/23 (UK)
5. Add user authentication and role-based access control
6. Migrate audit trail from SQLite to PostgreSQL for production scale
7. Implement data retention policy aligned to POCA 2002 (7-year minimum for AML records)

See `docs/responsible-ai-checklist.md` for the full governance framework.

---

## Background

Built by [Basavaraj Shepur](https://linkedin.com/in/basavarajshepur) — Senior AI Product Manager with 19 years in financial services. This system implements the responsible AI patterns used in global banks: confidence thresholds, human-in-the-loop gates, full audit chains, and explainability-first design.

---

## License

MIT

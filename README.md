# AML Copilot

**Multi-agent AML alert triage system** — enrichment, risk scoring, SAR drafting, HITL queue, and audit trail for financial crime compliance.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Status](https://img.shields.io/badge/Status-Production--Ready%20Demo-brightgreen) ![Claude](https://img.shields.io/badge/Powered%20by-Claude%20AI-orange)

---

## Executive Summary

### The Pain Points This Solves

**Pain Point 1 — The False Positive Avalanche**

Every bank runs automated software that monitors every transaction and flags anything suspicious. The problem is these systems are deliberately over-sensitive — they would rather flag 1,000 innocent transactions than miss one criminal one. The result: **95 to 99 out of every 100 alerts are false alarms.** A typical large bank employs 800 to 1,200 compliance analysts whose primary job, every single working day, is to dismiss legitimate transactions. They are not catching criminals — they are clearing a never-ending queue of noise. AML Copilot reads each alert, checks the customer and counterparty against sanctions lists and databases, assesses the risk, and gives a clear recommendation — often dismissing obvious false positives in under 30 seconds.

**Pain Point 2 — The Six-System Problem**

When an analyst receives an alert today, they must manually log into several different systems: a sanctions database, a PEP database, a news search tool, a country risk database, the bank's own customer records, and the transaction monitoring system. This context-switching takes 15–30 minutes per alert before the analyst has even begun thinking about whether the transaction is suspicious. AML Copilot gathers all of this automatically and presents it on a single screen before the analyst starts reviewing.

**Pain Point 3 — Inconsistent Decisions**

When hundreds of analysts review similar alerts, they make different decisions based on experience, fatigue, and workload. A transaction dismissed on a Monday morning may be escalated by a different analyst on a Friday afternoon. This inconsistency creates regulatory risk. AML Copilot applies the same logic, the same criteria, and the same reasoning to every single alert, every time — the 500th alert gets the same quality of analysis as the first.

**Pain Point 4 — SAR Drafting Takes Too Long**

Writing a Suspicious Activity Report (SAR) from scratch takes 60–90 minutes even for experienced analysts. AML Copilot automatically drafts the SAR in the correct regulatory format (FCA in the UK, FinCEN in the US) when a suspicious transaction is identified. The analyst reviews and approves — rather than writing from a blank page.

**Pain Point 5 — The Audit Trail Black Hole**

Regulators require documented rationale for every alert decision. In many institutions this documentation is incomplete or lives in spreadsheets that are difficult to produce during an inspection. AML Copilot automatically records every decision — AI recommendation and analyst final call — with a full timestamp, complete reasoning, and a unique audit reference. Any alert from any date can be produced in seconds.

**Pain Point 6 — Alert Fatigue Causes Real Misses**

When analysts spend eight hours per day dismissing false positives, they become fatigued. Their ability to spot genuinely suspicious transactions buried in noise degrades — the system designed to catch criminals ends up creating conditions where criminals are more likely to slip through. By handling obvious false positives automatically, AML Copilot reduces cognitive load on analysts so they focus on alerts that genuinely need a human eye.

---

### Business Value in Financial Services

**Cost Reduction**

| Metric | Before | After |
|---|---|---|
| Time to review one alert | 20–45 minutes | Under 10 minutes (AI pre-work done) |
| Alerts auto-dismissed at high confidence | 0% (all manual) | 60–70% |
| SAR drafting time | 60–90 minutes | Under 20 minutes |
| Audit trail completeness | Inconsistent | 100% of decisions logged |

If a bank employs 500 analysts and the tool halves average review time, that is the equivalent of 250 analysts' worth of capacity — without hiring a single person.

**Regulatory Fine Avoidance**

AML failures are among the most expensive regulatory breaches in financial services: HSBC ($1.9 billion), Standard Chartered ($1.1 billion), Deutsche Bank ($630 million), Westpac (AUD 1.3 billion). These fines are not just for failing to catch criminals — they are for inadequate processes, poor documentation, and inconsistent decision-making. AML Copilot directly addresses all three.

**Analyst Retention**

Compliance analyst turnover is a significant hidden cost. AML Copilot removes the monotonous parts of the job — repetitive false-positive dismissals, manual data gathering, SAR drafting from scratch — leaving analysts to do the intellectually engaging work they were hired for. Job satisfaction improves. Institutional knowledge is retained.

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

## Competitive Advantages

**1. Explainability First — Not a Black Box**

Many AI systems in financial services give an answer without explaining why. This is a fundamental problem in a regulated environment where every decision must be justified to a regulator. AML Copilot shows its working every time: a numbered reasoning chain, the specific red flags identified, the mitigating factors considered, and a confidence score. No decision is unexplained. Every recommendation is audit-ready.

**2. Human-in-the-Loop by Design, Not as an Afterthought**

The system is calibrated to route uncertainty to humans. Any decision where the AI is less than 85% confident is sent to the analyst queue — even if the AI recommends dismissal. A wrong auto-dismiss is just as costly as a wrong escalation. All SAR and ESCALATE decisions require human review without exception. No AI in this system can file a SAR. The analyst remains in control at all times. This is not just ethically correct — it is commercially essential. Regulators will not accept AI-only decisions in high-stakes compliance contexts.

**3. Consistency at Scale**

AML Copilot applies identical logic to every alert. The same transaction reviewed at 9am on Monday and 4pm on Friday gets the same risk score, the same reasoning, and the same routing decision. Human analysts are inconsistent; this system is not. Consistency is both an efficiency gain and a regulatory requirement — banks must demonstrate that their decision-making process is systematic and non-discriminatory.

**4. Full Audit Chain, Built In**

Before an analyst sees the AI recommendation, it is already written to the audit log. This means the bank has evidence of the AI's original recommendation regardless of what the analyst decides. If an analyst overrides the AI, both decisions are recorded — creating a complete, tamper-proof record that can be exported in minutes for regulatory submission.

**5. Covers All Major Money Laundering Typologies**

| Typology | Description |
|---|---|
| Structuring / Smurfing | Breaking large sums into smaller transactions just below reporting thresholds |
| Layering | Moving money rapidly through multiple accounts to obscure its origin |
| Trade-Based ML | Using import/export transactions with inflated or deflated invoices |
| PEP Transactions | Handling the heightened risk of politically exposed persons |
| Cryptocurrency Flows | Detecting suspicious crypto purchase patterns |
| Money Mule Networks | Identifying accounts used to receive and forward criminal proceeds |
| Shell Company Structures | Recognising BVI and offshore entity patterns used for concealment |

**6. Production-Ready Architecture**

Low-temperature AI reasoning (temperature 0.1) ensures the same alert produces the same decision every time. Sanctions screening covers OFAC (US), UN, EU, and HMT (UK) lists simultaneously. Real-world screening APIs (Worldcheck, ComplyAdvantage) can be swapped in by replacing the mock layer. The audit database is built for long-term retention aligned to the 7-year minimum required by POCA 2002 in the UK.

---

## Future Growth Opportunities

**Real-Time Transaction Screening**

The current version analyses alerts after they have been flagged. The natural next step is moving earlier in the process — screening transactions in real time before they complete. This enables the bank to block genuinely suspicious transactions before the money moves, which is significantly more effective than filing a SAR after the funds have already left.

**Customer Risk Rating**

AML Copilot currently analyses individual transactions. The next evolution is building a continuous risk profile for each customer — combining transaction history, enrichment data, behavioural patterns, and peer group comparisons to assign a dynamic risk score to every account. This is the shift from reactive (review alerts as they arrive) to proactive (monitor customers continuously).

**Network Analysis — Catching Rings, Not Just Individuals**

Money laundering rarely involves a single person or account. Criminal networks involve dozens of interconnected accounts, companies, and individuals. A future version would connect the dots — identifying when multiple accounts are part of the same criminal network, even when no individual transaction is large enough to trigger an alert on its own. This is graph-based network analysis: the AI spots the web, not just the individual strand.

**Regulatory Reporting Automation**

Beyond SAR drafting, there are numerous regular reports that compliance teams must submit to regulators: threshold transaction reports, high-value customer declarations, annual AML risk assessments. AML Copilot's report generation capability can be extended to automate the full suite of regulatory submissions, reducing the compliance team's reporting burden significantly.

**Cross-Institution Intelligence (With Privacy)**

Individual banks see only the transactions that flow through their own accounts. A suspicious customer who operates across three banks may not trigger alerts at any one of them individually. Future AML intelligence platforms will enable banks to share anonymised risk signals — without sharing customer data — so that the industry as a whole can identify threats no single institution could see alone.

**Expansion Into Adjacent Compliance Domains**

The same multi-agent architecture applies directly to:
- **Sanctions compliance** — real-time screening against OFAC/UN/EU/HMT
- **Fraud detection** — account takeover, application fraud, payment fraud
- **Market abuse surveillance** — insider dealing and market manipulation
- **KYC refresh** — automating periodic re-verification of customer identity and risk profile

**RegTech SaaS Platform**

AML Copilot can evolve from an internal tool into a platform offered to smaller financial institutions — challenger banks, payment firms, credit unions, and wealth managers — that cannot afford large compliance teams but face the same regulatory obligations. A SaaS version would serve this underserved market directly.

---

## Background

Built by [Basavaraj Shepur](https://linkedin.com/in/basavarajshepur) — Senior AI Product Manager with 19 years in financial services. This system implements the responsible AI patterns used in global banks: confidence thresholds, human-in-the-loop gates, full audit chains, and explainability-first design.

---

## License

MIT

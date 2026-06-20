# Responsible AI Checklist — AML Copilot

This checklist maps to FCA guidance on AI in financial services (FCA DP5/22) and
the Basel Committee's principles on operational risk for AI (2021).

---

## 1. Human Oversight

- [x] **HITL mandatory for high-risk decisions** — SAR and ESCALATE decisions always require analyst review
- [x] **HITL mandatory for low-confidence decisions** — Any AI confidence < 0.85 triggers human review
- [x] **AI recommendation presented before analyst input** — prevents anchoring in reverse
- [x] **Override is always available** — analyst can select any outcome regardless of AI recommendation
- [x] **Override requires documentation** — notes field mandatory for any non-agreement decision
- [x] **No automatic SAR filing** — narrative draft only; MLRO must review and file manually

## 2. Transparency and Explainability

- [x] **Structured reasoning chain** — every decision includes numbered reasoning factors
- [x] **Explicit red flags and mitigating factors** — not just a score
- [x] **Confidence score always shown** — analysts understand AI certainty level
- [x] **Enrichment data sources documented** — analysts know where data came from
- [x] **Typology match labelled** — connects alert to known AML pattern when applicable

## 3. Audit Trail Integrity

- [x] **AI decision logged before analyst review** — immutable record of what AI recommended
- [x] **Analyst decision logged with identity** — analyst_id required
- [x] **Final outcome always recorded** — what actually happened, regardless of AI recommendation
- [x] **Append-only audit trail** — no delete or update operations on logged decisions
- [x] **CSV export for regulatory submission** — FCA/FinCEN audit-ready format
- [x] **Timestamp precision** — UTC timestamps on all entries

## 4. Data Minimisation and Privacy

- [x] **No protected characteristics in enrichment** — race, religion, ethnicity never used as risk signals
- [x] **Enrichment limited to financial and regulatory facts** — sanctions status, PEP status, adverse media
- [x] **Customer data not sent to external services** — enrichment tools are mocked/internal in production
- [ ] **Data retention policy** — audit trail retention must align with firm's data governance policy (recommend 7 years for AML records per POCA 2002)

## 5. Model Risk

- [x] **Confidence thresholds defined and documented** — not arbitrary; tied to HITL routing logic
- [x] **Low temperature for risk analysis** — temperature 0.1 ensures consistency for same inputs
- [ ] **A/B testing framework** — recommend tracking AI vs. analyst decision alignment rate over time
- [ ] **Model drift monitoring** — recommend monthly review of override rate and decision distribution
- [ ] **SR 11-7 / SS1/23 model documentation** — if deployed at a regulated institution, formal model risk management process required

## 6. Bias and Fairness

- [x] **No customer demographic signals used** — alerts assessed on transaction behaviour only
- [x] **Reasoning must reference specific transaction facts** — prevents proxy discrimination
- [ ] **Fairness monitoring** — recommend tracking alert rates and escalation rates by customer segment post-deployment to detect disparate impact

## 7. Production Deployment Checklist (before go-live at a regulated firm)

- [ ] MRM validation under SR 11-7 / SS1/23
- [ ] Legal review of AI use in AML context
- [ ] MLRO sign-off on HITL thresholds
- [ ] IT security review of API key management
- [ ] Integration with production TMS (replace mock enrichment tools)
- [ ] User acceptance testing with AML analyst cohort
- [ ] Training programme for analyst users
- [ ] Incident response procedure for AI failure
- [ ] CCO and board-level AI governance sign-off

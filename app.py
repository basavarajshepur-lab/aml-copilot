"""
AML Copilot — HITL Review Interface

Streamlit app for AML analysts to review AI triage decisions,
override where needed, and maintain the audit trail.

Run: streamlit run app.py
"""

import json
import time
import streamlit as st
import pandas as pd
from pathlib import Path
from core.models import Alert, RiskDecision
from core.pipeline import process_alert
from core.audit_trail import get_dashboard_stats, get_audit_trail, log_analyst_decision, export_csv

st.set_page_config(
    page_title="AML Copilot",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
st.sidebar.title("🔍 AML Copilot")
st.sidebar.caption("Multi-agent AML alert triage • v1.0")
st.sidebar.divider()

stats = get_dashboard_stats()
st.sidebar.metric("Total Processed", stats["total_processed"])
st.sidebar.metric("Auto-Dismissed", stats["auto_dismissed"])
st.sidebar.metric("Escalated / SAR", stats["escalated"])
st.sidebar.metric("Pending Review", stats["pending_analyst_review"])
if stats["total_processed"] > 0:
    st.sidebar.metric(
        "Est. False Positive Rate",
        f"{stats['false_positive_rate_estimate']}%",
        help="Alerts auto-dismissed vs total processed"
    )

st.sidebar.divider()
if st.sidebar.button("📥 Export Audit Trail CSV"):
    path = export_csv()
    st.sidebar.success(f"Exported to {path}")

# --- Main tabs ---
tab_process, tab_batch, tab_audit = st.tabs(["🔎 Process Alert", "📋 Batch Process", "📜 Audit Trail"])

DECISION_COLORS = {
    "DISMISS": "🟢",
    "MONITOR": "🟡",
    "ESCALATE": "🟠",
    "SAR": "🔴",
}

# --- Tab 1: Process single alert ---
with tab_process:
    st.header("Process AML Alert")
    col1, col2 = st.columns([1, 1])

    with col1:
        sample_path = Path("data/sample_alerts.json")
        sample_alerts = json.loads(sample_path.read_text()) if sample_path.exists() else []
        alert_ids = [a["alert_id"] for a in sample_alerts]

        selected_id = st.selectbox("Select sample alert", alert_ids)
        alert_data = next((a for a in sample_alerts if a["alert_id"] == selected_id), None)

        if alert_data:
            with st.expander("Alert details", expanded=True):
                st.write(f"**Customer:** {alert_data['customer_name']}")
                st.write(f"**Amount:** {alert_data['amount']:,.2f} {alert_data['currency']}")
                st.write(f"**Transaction type:** {alert_data['transaction_type']}")
                st.write(f"**Counterparty:** {alert_data['counterparty_name']} ({alert_data['counterparty_country']})")
                st.write(f"**Rule triggered:** {alert_data['rule_triggered']}")
                st.write(f"**Account history:** {alert_data['account_history_summary']}")
                st.write(f"**Risk indicators:** {', '.join(alert_data['risk_indicators'])}")

    with col2:
        if st.button("▶ Run AI Triage", type="primary", use_container_width=True):
            if alert_data:
                alert = Alert(**alert_data)
                with st.spinner("Running enrichment + risk analysis..."):
                    start = time.time()
                    result = process_alert(alert)
                    elapsed = time.time() - start

                decision = result.triage_decision
                emoji = DECISION_COLORS.get(decision.decision.value, "⚪")

                st.success(f"Processed in {elapsed:.1f}s")

                st.subheader(f"{emoji} Decision: {decision.decision.value}")
                col_score, col_conf = st.columns(2)
                col_score.metric("Risk Score", f"{decision.risk_score}/100")
                col_conf.metric("AI Confidence", f"{decision.confidence:.0%}")

                if decision.confidence < 0.85:
                    st.warning("⚠️ Low confidence — mandatory analyst review required")

                with st.expander("🔍 Enrichment results"):
                    enriched = result.enriched_alert
                    if enriched.sanctions_hits:
                        st.error(f"🚨 {len(enriched.sanctions_hits)} sanctions hit(s)")
                        for hit in enriched.sanctions_hits:
                            st.write(f"- {hit.list_name}: {hit.match_type} match ({hit.match_score:.0%}) — {hit.entity_details}")
                    else:
                        st.success("✅ No sanctions hits")
                    st.write(f"**PEP status:** {'⚠️ YES — ' + enriched.pep_details if enriched.is_pep else '✅ No'}")
                    st.write(f"**Country risk:** {enriched.counterparty_country_risk.value}")
                    if enriched.adverse_media_findings:
                        st.warning("Adverse media: " + "; ".join(enriched.adverse_media_findings))

                with st.expander("🧠 AI Reasoning"):
                    st.write("**Red flags:**")
                    for flag in decision.key_red_flags:
                        st.write(f"• {flag}")
                    st.write("**Mitigating factors:**")
                    for factor in decision.mitigating_factors:
                        st.write(f"• {factor}")
                    st.write("**Reasoning chain:**")
                    for i, reason in enumerate(decision.reasoning, 1):
                        st.write(f"{i}. {reason}")
                    st.write("**Recommended actions:**")
                    for action in decision.recommended_actions:
                        st.write(f"→ {action}")

                if result.sar_narrative:
                    with st.expander("📋 SAR Narrative Draft (MLRO review required)"):
                        nar = result.sar_narrative
                        st.write(f"**Subject:** {nar.subject_information}")
                        st.write(f"**Transaction:** {nar.transaction_details}")
                        st.write(f"**Suspicious activity:** {nar.suspicious_activity_description}")
                        st.write(f"**Why suspicious:** {nar.why_suspicious}")
                        st.write(f"**Filing jurisdiction:** {nar.recommended_filing_jurisdiction}")

                if result.sent_to_hitl:
                    st.divider()
                    st.subheader("👤 Analyst Review")
                    analyst_id = st.text_input("Analyst ID", value="ANALYST_01")
                    analyst_decision = st.radio(
                        "Your decision",
                        ["AGREE WITH AI", "DISMISS", "MONITOR", "ESCALATE", "SAR"],
                        horizontal=True,
                    )
                    analyst_notes = st.text_area("Notes (required for overrides)")
                    if st.button("✅ Submit Review", type="primary"):
                        final = analyst_decision if analyst_decision != "AGREE WITH AI" else decision.decision.value
                        log_analyst_decision(
                            audit_id=result.audit_id,
                            analyst_id=analyst_id,
                            analyst_decision=analyst_decision,
                            analyst_notes=analyst_notes,
                            final_outcome=final,
                        )
                        st.success(f"Decision logged. Final outcome: {final}")

# --- Tab 2: Batch process ---
with tab_batch:
    st.header("Batch Process Alerts")
    st.info("Upload a JSON file of alerts (same format as sample_alerts.json) to process in bulk.")

    uploaded = st.file_uploader("Upload alerts JSON", type=["json"])
    if uploaded:
        alerts_data = json.load(uploaded)
        st.write(f"Found {len(alerts_data)} alerts")
        if st.button("▶ Process All", type="primary"):
            results = []
            progress = st.progress(0)
            for i, a in enumerate(alerts_data):
                alert = Alert(**a)
                result = process_alert(alert)
                results.append({
                    "Alert ID": result.alert_id,
                    "Decision": result.triage_decision.decision.value,
                    "Risk Score": result.triage_decision.risk_score,
                    "Confidence": f"{result.triage_decision.confidence:.0%}",
                    "HITL Required": "Yes" if result.sent_to_hitl else "No",
                    "Processing (ms)": result.processing_time_ms,
                })
                progress.progress((i + 1) / len(alerts_data))
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False)
            st.download_button("Download results CSV", csv, "batch_results.csv", "text/csv")

# --- Tab 3: Audit trail ---
with tab_audit:
    st.header("Audit Trail")
    alert_id_search = st.text_input("Search by Alert ID")
    if alert_id_search:
        trail = get_audit_trail(alert_id_search)
        if trail:
            for entry in trail:
                with st.expander(f"Stage: {entry['stage']} — {entry['timestamp']}"):
                    st.json(entry)
        else:
            st.info("No audit entries found for this alert ID")

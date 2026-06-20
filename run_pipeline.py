"""
CLI runner for AML Copilot pipeline.

Usage:
  python run_pipeline.py --alert data/sample_alerts.json --id ALERT_001
  python run_pipeline.py --batch data/sample_alerts.json
"""

import argparse
import json
import sys
from pathlib import Path
from core.models import Alert
from core.pipeline import process_alert


def print_result(result) -> None:
    decision = result.triage_decision
    print(f"\n{'='*60}")
    print(f"Alert ID : {result.alert_id}")
    print(f"Decision : {decision.decision.value}  (risk score: {decision.risk_score}/100)")
    print(f"Confidence: {decision.confidence:.0%}  |  HITL required: {result.sent_to_hitl}")
    print(f"Audit ID : {result.audit_id}")
    print(f"Processing: {result.processing_time_ms:.0f}ms")
    print(f"\nRed flags:")
    for flag in decision.key_red_flags:
        print(f"  • {flag}")
    print(f"\nReasoning:")
    for i, r in enumerate(decision.reasoning, 1):
        print(f"  {i}. {r}")
    if result.sar_narrative:
        print(f"\n⚠️  SAR narrative draft generated — MLRO review required before filing")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="AML Copilot — multi-agent alert triage")
    parser.add_argument("--alert", required=True, help="Path to alerts JSON file")
    parser.add_argument("--id", dest="alert_id", help="Process specific alert by ID")
    parser.add_argument("--batch", action="store_true", help="Process all alerts in file")
    args = parser.parse_args()

    path = Path(args.alert)
    if not path.exists():
        print(f"Error: file not found: {path}")
        sys.exit(1)

    alerts_data = json.loads(path.read_text())

    if args.alert_id:
        alert_data = next((a for a in alerts_data if a["alert_id"] == args.alert_id), None)
        if not alert_data:
            print(f"Alert {args.alert_id} not found in file")
            sys.exit(1)
        alert = Alert(**alert_data)
        result = process_alert(alert)
        print_result(result)

    elif args.batch:
        print(f"\nProcessing {len(alerts_data)} alerts...\n")
        decisions = {"DISMISS": 0, "MONITOR": 0, "ESCALATE": 0, "SAR": 0}
        for a in alerts_data:
            alert = Alert(**a)
            result = process_alert(alert)
            decisions[result.triage_decision.decision.value] += 1
            print_result(result)
        print("\nBatch Summary:")
        for d, count in decisions.items():
            print(f"  {d}: {count}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

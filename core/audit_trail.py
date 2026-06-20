"""
SQLite-backed audit trail for AML decisions.

Regulatory requirement: every AI recommendation and analyst override must be
logged with full context, timestamp, and identity. FCA and FinCEN auditors
will ask for this trail. Design principle: append-only, never delete.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import AuditEntry, EnrichedAlert, TriageDecision


DB_PATH = Path("audit.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialise_db() -> None:
    """Create audit table on first run. Idempotent."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                audit_id TEXT PRIMARY KEY,
                alert_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                stage TEXT NOT NULL,
                ai_decision TEXT,
                ai_confidence REAL,
                ai_reasoning TEXT,
                analyst_id TEXT,
                analyst_decision TEXT,
                analyst_notes TEXT,
                final_outcome TEXT,
                raw_payload TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_id ON audit_trail(alert_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_trail(timestamp)")


def log_ai_decision(
    alert_id: str,
    enriched_alert: EnrichedAlert,
    triage_decision: TriageDecision,
) -> str:
    """Log AI triage recommendation. Returns audit_id."""
    initialise_db()
    audit_id = str(uuid.uuid4())
    entry = AuditEntry(
        audit_id=audit_id,
        alert_id=alert_id,
        stage="ai_triage",
        ai_decision=triage_decision.decision.value,
        ai_confidence=triage_decision.confidence,
        ai_reasoning=json.dumps(triage_decision.reasoning),
    )
    with _get_connection() as conn:
        conn.execute(
            """INSERT INTO audit_trail VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                entry.audit_id,
                entry.alert_id,
                entry.timestamp.isoformat(),
                entry.stage,
                entry.ai_decision,
                entry.ai_confidence,
                entry.ai_reasoning,
                None, None, None, None,
                json.dumps({
                    "enriched_alert": enriched_alert.model_dump(mode="json"),
                    "triage_decision": triage_decision.model_dump(mode="json"),
                }),
            ),
        )
    return audit_id


def log_analyst_decision(
    audit_id: str,
    analyst_id: str,
    analyst_decision: str,
    analyst_notes: str,
    final_outcome: str,
) -> None:
    """Record analyst's HITL review decision against the existing AI log entry."""
    initialise_db()
    with _get_connection() as conn:
        conn.execute(
            """UPDATE audit_trail
               SET analyst_id=?, analyst_decision=?, analyst_notes=?, final_outcome=?
               WHERE audit_id=?""",
            (analyst_id, analyst_decision, analyst_notes, final_outcome, audit_id),
        )


def get_audit_trail(alert_id: str) -> list[dict]:
    """Return full audit trail for an alert (for regulatory review)."""
    initialise_db()
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_trail WHERE alert_id=? ORDER BY timestamp",
            (alert_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_dashboard_stats() -> dict:
    """Summary stats for the Streamlit dashboard."""
    initialise_db()
    with _get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM audit_trail WHERE stage='ai_triage'").fetchone()[0]
        dismissed = conn.execute("SELECT COUNT(*) FROM audit_trail WHERE ai_decision='DISMISS'").fetchone()[0]
        escalated = conn.execute("SELECT COUNT(*) FROM audit_trail WHERE ai_decision IN ('ESCALATE','SAR')").fetchone()[0]
        pending_hitl = conn.execute(
            "SELECT COUNT(*) FROM audit_trail WHERE stage='ai_triage' AND analyst_decision IS NULL"
        ).fetchone()[0]
    return {
        "total_processed": total,
        "auto_dismissed": dismissed,
        "escalated": escalated,
        "pending_analyst_review": pending_hitl,
        "false_positive_rate_estimate": round(dismissed / total * 100, 1) if total else 0,
    }


def export_csv(output_path: str = "audit_export.csv") -> str:
    """Export audit trail to CSV for regulatory submission."""
    import csv
    initialise_db()
    with _get_connection() as conn:
        rows = conn.execute("SELECT * FROM audit_trail ORDER BY timestamp").fetchall()
    with open(output_path, "w", newline="") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=dict(rows[0]).keys())
            writer.writeheader()
            writer.writerows([dict(r) for r in rows])
    return output_path

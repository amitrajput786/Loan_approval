import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "workflow.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            request_id TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            applicant_name TEXT,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            rules_triggered TEXT,
            message TEXT,
            data_snapshot TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        );

        CREATE TABLE IF NOT EXISTS state_history (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        );
    """)
    conn.commit()
    conn.close()


def create_application(request_id: str, data: dict) -> dict:
    app_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    conn.execute(
        "INSERT INTO applications (id, request_id, status, applicant_name, data, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (app_id, request_id, "pending", data.get("applicant_name", ""), json.dumps(data), now, now)
    )
    conn.commit()
    conn.close()
    return {"id": app_id, "request_id": request_id, "status": "pending", "data": data, "created_at": now}


def get_application_by_request_id(request_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM applications WHERE request_id = ?", (request_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_application_by_id(app_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_status(app_id: str, new_status: str, reason: str = None):
    conn = get_conn()
    old = conn.execute("SELECT status FROM applications WHERE id = ?", (app_id,)).fetchone()
    now = datetime.utcnow().isoformat()
    conn.execute("UPDATE applications SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, app_id))
    conn.execute(
        "INSERT INTO state_history (id, application_id, from_status, to_status, reason, created_at) VALUES (?,?,?,?,?,?)",
        (str(uuid.uuid4()), app_id, old["status"] if old else None, new_status, reason, now)
    )
    conn.commit()
    conn.close()


def add_audit(app_id: str, stage: str, status: str, rules_triggered: list, message: str, data_snapshot: dict = None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO audit_log (id, application_id, stage, status, rules_triggered, message, data_snapshot, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), app_id, stage, status, json.dumps(rules_triggered), message, json.dumps(data_snapshot or {}), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def get_audit_trail(app_id: str) -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM audit_log WHERE application_id = ? ORDER BY created_at", (app_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_state_history(app_id: str) -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM state_history WHERE application_id = ? ORDER BY created_at", (app_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_applications(status: str = None) -> list:
    conn = get_conn()
    if status:
        rows = conn.execute("SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM applications ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
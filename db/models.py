import sqlite3
import uuid
from datetime import datetime
from config import DB_PATH


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --- Cases ---

def create_case(title: str, category: str, description: str = "") -> str:
    case_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO cases (id, title, category, description) VALUES (?, ?, ?, ?)",
            (case_id, title, category, description)
        )
    return case_id


def get_cases() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_case(case_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    return dict(row) if row else None


def update_case_description(case_id: str, description: str):
    with _conn() as conn:
        conn.execute(
            "UPDATE cases SET description = ?, updated_at = ? WHERE id = ?",
            (description, datetime.now(), case_id)
        )


# --- Documents ---

def add_document(case_id: str, filename: str, file_type: str, upload_path: str) -> str:
    doc_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO documents (id, case_id, filename, file_type, upload_path) VALUES (?, ?, ?, ?, ?)",
            (doc_id, case_id, filename, file_type, upload_path)
        )
    return doc_id


def get_documents(case_id: str) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM documents WHERE case_id = ? ORDER BY created_at DESC", (case_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# --- Timeline Events ---

def add_timeline_event(case_id: str, title: str, event_type: str = "Note",
                        description: str = "", event_date: str = None) -> str:
    event_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO timeline_events (id, case_id, event_type, title, description, event_date) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, case_id, event_type, title, description, event_date)
        )
    return event_id


def get_timeline(case_id: str) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM timeline_events WHERE case_id = ? ORDER BY event_date ASC, created_at ASC",
            (case_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_event_status(event_id: str, status: str):
    with _conn() as conn:
        conn.execute("UPDATE timeline_events SET status = ? WHERE id = ?", (status, event_id))


def delete_timeline_event(event_id: str):
    with _conn() as conn:
        conn.execute("DELETE FROM timeline_events WHERE id = ?", (event_id,))


# --- Drafts ---

def save_draft(case_id: str, draft_type: str, title: str, content: str) -> str:
    draft_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO drafts (id, case_id, draft_type, title, content) VALUES (?, ?, ?, ?, ?)",
            (draft_id, case_id, draft_type, title, content)
        )
    return draft_id


def get_drafts(case_id: str) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM drafts WHERE case_id = ? ORDER BY created_at DESC", (case_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def delete_draft(draft_id: str):
    with _conn() as conn:
        conn.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))


# --- Chat History ---

def save_message(role: str, content: str, case_id: str = None) -> str:
    msg_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO chat_history (id, case_id, role, content) VALUES (?, ?, ?, ?)",
            (msg_id, case_id, role, content)
        )
    return msg_id


def get_chat_history(case_id: str = None, limit: int = 20) -> list[dict]:
    with _conn() as conn:
        if case_id:
            rows = conn.execute(
                "SELECT * FROM chat_history WHERE case_id = ? ORDER BY created_at DESC LIMIT ?",
                (case_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM chat_history WHERE case_id IS NULL ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [dict(r) for r in reversed(rows)]

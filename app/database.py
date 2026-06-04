import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL DEFAULT '',
            is_completed INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            due_date TEXT,
            alarm_time TEXT,
            is_alarmed INTEGER NOT NULL DEFAULT 0,
            audio_file TEXT,
            duration INTEGER DEFAULT 0,
            transcribed_text TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            service TEXT PRIMARY KEY,
            key_value TEXT NOT NULL
        );
    """)
    # Add completed_at column for existing databases
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN completed_at TEXT")
    except Exception:
        pass
    conn.close()


# ---- Tasks CRUD ----

def add_task(content="", due_date=None, alarm_time=None,
             audio_file=None, duration=0, transcribed_text=None):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO tasks (content, due_date, alarm_time, audio_file, duration, transcribed_text)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (content, due_date, alarm_time, audio_file, duration, transcribed_text),
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_all_tasks(filter_date=None, show_completed=False):
    """Get tasks, optionally filtered by date or completion status."""
    conn = get_connection()
    conditions = []
    params = []

    if not show_completed:
        conditions.append("is_completed=0")

    if filter_date == "today":
        today = date.today().strftime("%Y-%m-%d")
        conditions.append("(due_date=? OR due_date IS NULL)")
        params.append(today)
    elif filter_date == "tomorrow":
        tomorrow = date.today().isoformat()
        conditions.append("due_date=?")
        params.append(tomorrow)
    elif filter_date == "completed":
        conditions.append("is_completed=1")

    where = " AND ".join(conditions) if conditions else "1"
    query = f"SELECT * FROM tasks WHERE {where} ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_task(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_task(task_id, **kwargs):
    """Update task fields. Pass field=value for each field to update."""
    allowed = {"content", "is_completed", "due_date", "alarm_time",
               "is_alarmed", "audio_file", "duration", "transcribed_text"}
    fields = []
    values = []
    for key, val in kwargs.items():
        if key in allowed and val is not None:
            fields.append(f"{key}=?")
            values.append(val)
    if not fields:
        return
    values.append(task_id)
    conn = get_connection()
    conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", values)
    conn.commit()
    conn.close()


def toggle_task(task_id):
    conn = get_connection()
    row = conn.execute("SELECT is_completed FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        conn.close()
        return
    if row["is_completed"]:
        conn.execute("UPDATE tasks SET is_completed=0, completed_at=NULL WHERE id=?", (task_id,))
    else:
        conn.execute("UPDATE tasks SET is_completed=1, completed_at=datetime('now','localtime') WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_connection()
    row = conn.execute("SELECT audio_file FROM tasks WHERE id=?", (task_id,)).fetchone()
    audio_file = row["audio_file"] if row else None
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return audio_file


# ---- Task counts ----

def get_task_counts():
    """Get counts for all, today (incomplete), and completed tasks."""
    today = date.today().strftime("%Y-%m-%d")
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_completed=0").fetchone()[0]
    today_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_completed=0 AND due_date=?", (today,)).fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_completed=1").fetchone()[0]
    conn.close()
    return {"all": total, "today": today_count, "completed": done}


# ---- Alarms ----

def get_due_alarms():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE is_completed=0 AND is_alarmed=0 AND alarm_time IS NOT NULL AND alarm_time <= ?",
        (now,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_alarmed(task_id):
    conn = get_connection()
    conn.execute("UPDATE tasks SET is_alarmed=1 WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


# ---- API Keys ----

def save_api_key(service, key_value):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO api_keys (service, key_value) VALUES (?, ?)",
        (service, key_value),
    )
    conn.commit()
    conn.close()


def get_api_key(service):
    conn = get_connection()
    row = conn.execute("SELECT key_value FROM api_keys WHERE service=?", (service,)).fetchone()
    conn.close()
    return row["key_value"] if row else ""


def delete_api_key(service):
    conn = get_connection()
    conn.execute("DELETE FROM api_keys WHERE service=?", (service,))
    conn.commit()
    conn.close()

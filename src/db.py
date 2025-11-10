import sqlite3, threading
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path.home() / ".queuectl.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
_init_lock = threading.Lock()

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    command TEXT NOT NULL,
    state TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    run_after INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workers (
    pid INTEGER PRIMARY KEY,
    started_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_state_runafter ON jobs(state, run_after);
"""

def init_db():
    """Initialize database tables and default config values."""
    with _init_lock:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.executescript(SCHEMA)
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO config(key,value) VALUES('max_retries','3')")
        cur.execute("INSERT OR IGNORE INTO config(key,value) VALUES('backoff_base','2')")
        conn.commit()
        conn.close()

@contextmanager
def get_conn():
    """Provide a thread-safe DB connection."""
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    try:
        yield conn
    finally:
        conn.close()

def enqueue_job(job_id, command, ts_now):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO jobs(id, command, state, attempts, created_at, updated_at) VALUES(?,?,?,?,?,?)",
            (job_id, command, "pending", 0, ts_now, ts_now),
        )
        conn.commit()

def fetch_next_job(ts_now):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT id, command, attempts FROM jobs WHERE state='pending' AND run_after<=? ORDER BY created_at LIMIT 1",
            (ts_now,),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return None
        job_id, command, attempts = row
        cur.execute("UPDATE jobs SET state='processing', updated_at=? WHERE id=?", (ts_now, job_id))
        conn.commit()
        return {"id": job_id, "command": command, "attempts": attempts}

def mark_completed(job_id, ts_now):
    with get_conn() as conn:
        conn.execute("UPDATE jobs SET state='completed', updated_at=? WHERE id=?", (ts_now, job_id))
        conn.commit()

def mark_failed(job_id, error, attempts, run_after, ts_now):
    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET state='failed', last_error=?, attempts=?, run_after=?, updated_at=? WHERE id=?",
            (error, attempts, run_after, ts_now, job_id),
        )
        conn.commit()

def move_dead(job_id, error, ts_now):
    with get_conn() as conn:
        conn.execute("UPDATE jobs SET state='dead', last_error=?, updated_at=? WHERE id=?", (error, ts_now, job_id))
        conn.commit()

def list_jobs(state=None):
    with get_conn() as conn:
        cur = conn.cursor()
        if state:
            cur.execute("SELECT id, command, state, attempts, last_error FROM jobs WHERE state=?", (state,))
        else:
            cur.execute("SELECT id, command, state, attempts, last_error FROM jobs")
        return cur.fetchall()

def set_cfg(key, value):
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO config(key,value) VALUES(?,?)", (key, value))
        conn.commit()

def get_cfg(key):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM config WHERE key=?", (key,))
        res = cur.fetchone()
        return res[0] if res else None

def add_worker(pid, ts_now):
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO workers(pid, started_at) VALUES(?,?)", (pid, ts_now))
        conn.commit()

def rem_worker(pid):
    with get_conn() as conn:
        conn.execute("DELETE FROM workers WHERE pid=?", (pid,))
        conn.commit()

def list_workers():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT pid, started_at FROM workers")
        return cur.fetchall()

def get_job(job_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, command, state, attempts, last_error, run_after FROM jobs WHERE id=?", (job_id,))
        return cur.fetchone()

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.spectre/spectre.db")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS engagements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            target      TEXT NOT NULL,
            type        TEXT NOT NULL,       -- external | internal | web | ad
            scope       TEXT,
            notes       TEXT,
            status      TEXT DEFAULT 'active',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tool_runs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id   INTEGER NOT NULL,
            tool_name       TEXT NOT NULL,
            command         TEXT,
            kwargs          TEXT,            -- JSON
            stdout          TEXT,
            stderr          TEXT,
            success         INTEGER,
            elapsed_seconds INTEGER,
            timestamp       TEXT,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id)
        );

        CREATE TABLE IF NOT EXISTS findings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id   INTEGER NOT NULL,
            title           TEXT NOT NULL,
            description     TEXT,
            severity        TEXT,            -- critical | high | medium | low | info
            ttp             TEXT,            -- MITRE ATT&CK TTP id
            evidence        TEXT,
            host            TEXT,
            port            INTEGER,
            tool            TEXT,
            status          TEXT DEFAULT 'open',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id)
        );
    """)

    conn.commit()
    conn.close()


class Store:
    def __init__(self):
        init_db()

    def new_engagement(self, name, target, eng_type, scope="", notes="") -> int:
        conn = get_conn()
        now = datetime.now().isoformat()
        c = conn.cursor()
        c.execute(
            "INSERT INTO engagements (name, target, type, scope, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (name, target, eng_type, scope, notes, now, now)
        )
        conn.commit()
        eid = c.lastrowid
        conn.close()
        return eid

    def list_engagements(self) -> list:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM engagements ORDER BY created_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_engagement(self, eid: int) -> dict:
        conn = get_conn()
        row = conn.execute("SELECT * FROM engagements WHERE id=?", (eid,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def save_tool_run(self, engagement_id, tool_name, kwargs, result) -> int:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            """INSERT INTO tool_runs
               (engagement_id, tool_name, command, kwargs, stdout, stderr, success, elapsed_seconds, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                engagement_id,
                tool_name,
                result.get("command", ""),
                json.dumps(kwargs),
                result.get("stdout", ""),
                result.get("stderr", ""),
                1 if result.get("success") else 0,
                result.get("elapsed_seconds", 0),
                result.get("timestamp", datetime.now().isoformat()),
            )
        )
        conn.commit()
        rid = c.lastrowid
        conn.close()
        return rid

    def add_finding(self, engagement_id, title, description="", severity="medium",
                    ttp="", evidence="", host="", port=None, tool="") -> int:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            """INSERT INTO findings
               (engagement_id, title, description, severity, ttp, evidence, host, port, tool, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (engagement_id, title, description, severity, ttp,
             evidence, host, port, tool, datetime.now().isoformat())
        )
        conn.commit()
        fid = c.lastrowid
        conn.close()
        return fid

    def list_findings(self, engagement_id) -> list:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM findings WHERE engagement_id=? ORDER BY severity DESC",
            (engagement_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def list_tool_runs(self, engagement_id) -> list:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM tool_runs WHERE engagement_id=? ORDER BY timestamp ASC",
            (engagement_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_engagement(self, engagement_id: int) -> bool:
        """Delete an engagement and all associated findings and tool runs."""
        conn = get_conn()
        c = conn.cursor()
        try:
            # Delete findings associated with this engagement
            c.execute("DELETE FROM findings WHERE engagement_id=?", (engagement_id,))
            # Delete tool runs associated with this engagement
            c.execute("DELETE FROM tool_runs WHERE engagement_id=?", (engagement_id,))
            # Delete the engagement itself
            c.execute("DELETE FROM engagements WHERE id=?", (engagement_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting engagement: {e}")
            return False
        finally:
            conn.close()

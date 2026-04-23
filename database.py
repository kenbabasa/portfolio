import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = "meetings.db"

# ── DB CONNECTION ──────────────────────────────────────────────
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL") # safe for concurrent writes
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── INIT (call once on startup) ────────────────────────────────
def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS meetings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                token       TEXT    UNIQUE NOT NULL,
                name        TEXT    NOT NULL,
                email       TEXT    NOT NULL,
                date        TEXT    NOT NULL,   -- YYYY-MM-DD
                time        TEXT    NOT NULL,   -- HH:MM
                duration    INTEGER NOT NULL,   -- minutes
                topic       TEXT    NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'pending',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS blocked_dates (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT    NOT NULL,   -- YYYY-MM-DD  (block whole day)
                time_from   TEXT,               -- HH:MM  NULL = whole day
                time_to     TEXT,               -- HH:MM  NULL = whole day
                reason      TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(date, time_from, time_to)
            );
        """)
    print("✅ Database initialised →", DB_PATH)


# ══════════════════════════════════════════════════════════════
#  MEETINGS
# ══════════════════════════════════════════════════════════════

def save_meeting(token: str, meeting: dict) -> bool:
    """Insert a new meeting.  Returns False if the slot is already taken."""
    if not is_slot_available(meeting["date"], meeting["time"], meeting["duration"]):
        return False
    with get_db() as conn:
        conn.execute(
            """INSERT INTO meetings (token, name, email, date, time, duration, topic, status)
               VALUES (:token, :name, :email, :date, :time, :duration, :topic, 'pending')""",
            {**meeting, "token": token},
        )
    return True


def get_meeting(token: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM meetings WHERE token = ?", (token,)
        ).fetchone()
    return dict(row) if row else None


def update_meeting_status(token: str, status: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE meetings SET status = ? WHERE token = ?", (status, token)
        )


def get_all_meetings(status: str | None = None) -> list[dict]:
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM meetings WHERE status = ? ORDER BY date, time", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM meetings ORDER BY date, time"
            ).fetchall()
    return [dict(r) for r in rows]


# ── CONFLICT CHECK ─────────────────────────────────────────────
def is_slot_available(date: str, time: str, duration: int | str, exclude_token: str | None = None) -> bool:
    """
    Returns True only if:
      • no confirmed/pending meeting overlaps the requested window, AND
      • the date/time is not blocked by the owner.
    """
    duration = int(duration)
    req_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    req_end   = req_start + timedelta(minutes=duration)

    # 1. Check existing meetings
    with get_db() as conn:
        rows = conn.execute(
            """SELECT time, duration FROM meetings
               WHERE date = ? AND status IN ('pending','confirmed')
               AND token IS NOT ?""",
            (date, exclude_token),
        ).fetchall()

    for row in rows:
        ex_start = datetime.strptime(f"{date} {row['time']}", "%Y-%m-%d %H:%M")
        ex_end   = ex_start + timedelta(minutes=int(row["duration"]))
        # overlap if one starts before the other ends
        if req_start < ex_end and req_end > ex_start:
            return False

    # 2. Check blocked dates / times
    with get_db() as conn:
        blocks = conn.execute(
            "SELECT time_from, time_to FROM blocked_dates WHERE date = ?", (date,)
        ).fetchall()

    for block in blocks:
        if block["time_from"] is None:          # whole day blocked
            return False
        bl_start = datetime.strptime(f"{date} {block['time_from']}", "%Y-%m-%d %H:%M")
        bl_end   = datetime.strptime(f"{date} {block['time_to']}",   "%Y-%m-%d %H:%M")
        if req_start < bl_end and req_end > bl_start:
            return False

    return True


def get_booked_slots(date: str) -> list[dict]:
    """Return all active slots on a given date (for the calendar UI)."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT time, duration FROM meetings
               WHERE date = ? AND status IN ('pending','confirmed')""",
            (date,),
        ).fetchall()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════
#  BLOCKED DATES  (owner manages these)
# ══════════════════════════════════════════════════════════════

def block_date(date: str, time_from: str | None = None, time_to: str | None = None, reason: str = "") -> bool:
    """
    Block a whole day (time_from=None) or a specific window.
    Returns False if the exact same block already exists.
    """
    try:
        with get_db() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO blocked_dates (date, time_from, time_to, reason)
                   VALUES (?, ?, ?, ?)""",
                (date, time_from, time_to, reason),
            )
        return True
    except Exception:
        return False


def unblock_date(date: str, time_from: str | None = None, time_to: str | None = None) -> bool:
    with get_db() as conn:
        conn.execute(
            "DELETE FROM blocked_dates WHERE date=? AND time_from IS ? AND time_to IS ?",
            (date, time_from, time_to),
        )
    return True


def get_blocked_dates() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM blocked_dates ORDER BY date, time_from"
        ).fetchall()
    return [dict(r) for r in rows]


def get_blocked_for_month(year: int, month: int) -> list[dict]:
    """Return blocked entries for a calendar month (YYYY-MM)."""
    prefix = f"{year}-{str(month).zfill(2)}"
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM blocked_dates WHERE date LIKE ?", (f"{prefix}%",)
        ).fetchall()
    return [dict(r) for r in rows]
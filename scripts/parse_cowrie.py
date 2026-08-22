#!/usr/bin/env python3
"""
Cowrie Honeypot Log Parser
----------------------------------
Reads cowrie.json (JSON Lines format) and loads events into a SQLite
database across three tables: sessions, login_attempts, commands.

Safe to re-run: uses INSERT OR IGNORE with unique constraints so
re-parsing the same log file will not create duplicate rows.

Usage:
    python3 parse_cowrie.py /path/to/cowrie.json /path/to/cowrie.db
"""

import json
import sqlite3
import sys
from datetime import datetime


def create_tables(conn):
    """Create the three tables if they don't already exist."""
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id   TEXT PRIMARY KEY,
            src_ip       TEXT,
            start_time   TEXT,
            end_time     TEXT,
            duration_ms  INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT,
            username    TEXT,
            password    TEXT,
            success     INTEGER,
            timestamp   TEXT,
            UNIQUE(session_id, username, password, timestamp)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT,
            command     TEXT,
            timestamp   TEXT,
            UNIQUE(session_id, command, timestamp)
        )
    """)

    conn.commit()


def parse_line(line):
    """Parse a single line of cowrie.json. Returns dict or None if malformed."""
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def process_event(conn, event):
    """Route a single parsed event to the correct table."""
    eventid = event.get("eventid", "")
    session_id = event.get("session")
    timestamp = event.get("timestamp")
    src_ip = event.get("src_ip")

    cur = conn.cursor()

    if eventid == "cowrie.session.connect":
        cur.execute("""
            INSERT OR IGNORE INTO sessions (session_id, src_ip, start_time)
            VALUES (?, ?, ?)
        """, (session_id, src_ip, timestamp))

    elif eventid == "cowrie.session.closed":
        duration_ms = event.get("duration")
        cur.execute("""
            UPDATE sessions
            SET end_time = ?, duration_ms = ?
            WHERE session_id = ?
        """, (timestamp, duration_ms, session_id))

    elif eventid in ("cowrie.login.success", "cowrie.login.failed"):
        username = event.get("username")
        password = event.get("password")
        success = 1 if eventid == "cowrie.login.success" else 0
        cur.execute("""
            INSERT OR IGNORE INTO login_attempts
                (session_id, username, password, success, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, username, password, success, timestamp))

    elif eventid == "cowrie.command.input":
        command = event.get("input")
        cur.execute("""
            INSERT OR IGNORE INTO commands (session_id, command, timestamp)
            VALUES (?, ?, ?)
        """, (session_id, command, timestamp))


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 parse_cowrie.py <cowrie.json> <cowrie.db>")
        sys.exit(1)

    json_path = sys.argv[1]
    db_path = sys.argv[2]

    conn = sqlite3.connect(db_path)
    create_tables(conn)

    total_lines = 0
    processed = 0
    skipped = 0

    with open(json_path, "r", errors="replace") as f:
        for line in f:
            total_lines += 1
            event = parse_line(line)
            if event is None:
                skipped += 1
                continue
            process_event(conn, event)
            processed += 1

    conn.commit()

    cur = conn.cursor()
    session_count = cur.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    attempt_count = cur.execute("SELECT COUNT(*) FROM login_attempts").fetchone()[0]
    command_count = cur.execute("SELECT COUNT(*) FROM commands").fetchone()[0]

    conn.close()

    print(f"Done. [{datetime.now().isoformat(timespec='seconds')}]")
    print(f"  Lines read:      {total_lines}")
    print(f"  Events processed: {processed}")
    print(f"  Lines skipped:   {skipped}")
    print("---")
    print(f"  sessions:        {session_count}")
    print(f"  login_attempts:  {attempt_count}")
    print(f"  commands:        {command_count}")


if __name__ == "__main__":
    main()

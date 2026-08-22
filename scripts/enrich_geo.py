#!/usr/bin/env python3
import sqlite3
import sys
import json
import urllib.request


BATCH_URL = "http://ip-api.com/batch"
BATCH_SIZE = 100


def create_geo_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ip_geo (
            ip           TEXT PRIMARY KEY,
            country      TEXT,
            country_code TEXT,
            city         TEXT,
            isp          TEXT,
            org          TEXT,
            is_hosting   INTEGER
        )
    """)
    conn.commit()


def get_unlooked_ips(conn):
    rows = conn.execute("""
        SELECT DISTINCT s.src_ip
        FROM sessions s
        LEFT JOIN ip_geo g ON s.src_ip = g.ip
        WHERE s.src_ip IS NOT NULL AND g.ip IS NULL
    """).fetchall()
    return [r[0] for r in rows]


def lookup_batch(ips):
    payload = json.dumps([
        {"query": ip, "fields": "status,country,countryCode,city,isp,org,hosting,query"}
        for ip in ips
    ]).encode("utf-8")

    req = urllib.request.Request(
        BATCH_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 enrich_geo.py <cowrie.db>")
        sys.exit(1)

    db_path = sys.argv[1]
    conn = sqlite3.connect(db_path)
    create_geo_table(conn)

    ips = get_unlooked_ips(conn)
    print(f"Found {len(ips)} IPs needing geo lookup.")

    if not ips:
        print("Nothing new to look up.")
        conn.close()
        return

    total_done = 0
    for i in range(0, len(ips), BATCH_SIZE):
        chunk = ips[i:i + BATCH_SIZE]
        try:
            results = lookup_batch(chunk)
        except Exception as e:
            print(f"Batch failed ({e}), skipping this chunk.")
            continue

        for r in results:
            if r.get("status") != "success":
                continue
            conn.execute("""
                INSERT OR REPLACE INTO ip_geo
                    (ip, country, country_code, city, isp, org, is_hosting)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("query"),
                r.get("country"),
                r.get("countryCode"),
                r.get("city"),
                r.get("isp"),
                r.get("org"),
                1 if r.get("hosting") else 0,
            ))
        total_done += len(chunk)
        conn.commit()
        print(f"  Looked up {total_done}/{len(ips)}...")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()

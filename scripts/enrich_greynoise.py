import sqlite3
import requests
import time

DB_PATH = "/home/jakob/cowrie-logs/cowrie.db"

def main():
    conn = sqlite3.connect(DB_PATH)

    # Create greynoise table if it doesn't exist yet
    conn.execute("""
        CREATE TABLE IF NOT EXISTS greynoise_data (
            ip TEXT PRIMARY KEY,
            noise INTEGER,
            riot INTEGER,
            classification TEXT
        )
    """)
    conn.commit()

    # Get all unique source IPs from sessions
    ips = [row[0] for row in conn.execute(
        "SELECT DISTINCT src_ip FROM sessions WHERE src_ip IS NOT NULL"
    )]

    print(f"Looking up {len(ips)} unique IPs in GreyNoise...")

    for i, ip in enumerate(ips):
        try:
            r = requests.get(
                f"https://api.greynoise.io/v3/community/{ip}",
                timeout=5
            )

            if r.status_code == 200:
                data = r.json()
                noise = 1 if data.get("noise") else 0
                riot = 1 if data.get("riot") else 0
                classification = data.get("classification", "unknown")
            else:
                # IP not in GreyNoise dataset
                noise, riot, classification = 0, 0, "unknown"

            conn.execute("""
                INSERT OR REPLACE INTO greynoise_data
                    (ip, noise, riot, classification)
                VALUES (?, ?, ?, ?)
            """, (ip, noise, riot, classification))
            conn.commit()

            print(f"  [{i+1}/{len(ips)}] {ip} — noise={bool(noise)}, classification={classification}")

            # Be polite — 1 request per second
            time.sleep(1)

        except Exception as e:
            print(f"  [{i+1}/{len(ips)}] {ip} — ERROR: {e}")
            continue

    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
import sqlite3
from flask import Flask, render_template, jsonify

app = Flask(__name__)
DB_PATH = "/home/jakob/cowrie-logs/cowrie.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/attempts_over_time")
def attempts_over_time():
    conn = get_db()
    rows = conn.execute("""
        SELECT date(timestamp) AS day, COUNT(*) AS attempts
        FROM login_attempts
        GROUP BY day
        ORDER BY day
    """).fetchall()
    conn.close()
    return jsonify([{"day": r["day"], "attempts": r["attempts"]} for r in rows])


@app.route("/api/top_ips")
def top_ips():
    conn = get_db()
    rows = conn.execute("""
        SELECT src_ip, COUNT(*) AS session_count
        FROM sessions
        WHERE src_ip IS NOT NULL
        GROUP BY src_ip
        ORDER BY session_count DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify([{"ip": r["src_ip"], "count": r["session_count"]} for r in rows])


@app.route("/api/top_credentials")
def top_credentials():
    conn = get_db()
    rows = conn.execute("""
        SELECT username, password, COUNT(*) AS attempts
        FROM login_attempts
        GROUP BY username, password
        ORDER BY attempts DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify([
        {"username": r["username"], "password": r["password"], "count": r["attempts"]}
        for r in rows
    ])


@app.route("/api/top_commands")
def top_commands():
    conn = get_db()
    rows = conn.execute("""
        SELECT command, COUNT(*) AS count
        FROM commands
        GROUP BY command
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify([{"command": r["command"], "count": r["count"]} for r in rows])


@app.route("/api/top_countries")
def top_countries():
    conn = get_db()
    rows = conn.execute("""
        SELECT g.country, g.country_code, COUNT(*) AS session_count
        FROM sessions s
        JOIN ip_geo g ON s.src_ip = g.ip
        WHERE g.country IS NOT NULL
        GROUP BY g.country
        ORDER BY session_count DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify([
        {"country": r["country"], "code": r["country_code"], "count": r["session_count"]}
        for r in rows
    ])


@app.route("/api/attacker_infra")
def attacker_infra():
    conn = get_db()
    rows = conn.execute("""
        SELECT g.org, g.isp, g.country, g.is_hosting, COUNT(*) AS session_count
        FROM sessions s
        JOIN ip_geo g ON s.src_ip = g.ip
        WHERE g.org IS NOT NULL AND g.org != ''
        GROUP BY g.org
        ORDER BY session_count DESC
        LIMIT 10
    """).fetchall()

    hosting_count = conn.execute("""
        SELECT COUNT(DISTINCT s.src_ip)
        FROM sessions s JOIN ip_geo g ON s.src_ip = g.ip
        WHERE g.is_hosting = 1
    """).fetchone()[0]
    residential_count = conn.execute("""
        SELECT COUNT(DISTINCT s.src_ip)
        FROM sessions s JOIN ip_geo g ON s.src_ip = g.ip
        WHERE g.is_hosting = 0
    """).fetchone()[0]

    conn.close()
    return jsonify({
        "top_orgs": [
            {"org": r["org"], "isp": r["isp"], "country": r["country"], "count": r["session_count"]}
            for r in rows
        ],
        "hosting_count": hosting_count,
        "residential_count": residential_count,
    })


@app.route("/api/summary")
def summary():
    conn = get_db()
    total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    total_attempts = conn.execute("SELECT COUNT(*) FROM login_attempts").fetchone()[0]
    total_success = conn.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE success = 1"
    ).fetchone()[0]
    unique_ips = conn.execute(
        "SELECT COUNT(DISTINCT src_ip) FROM sessions"
    ).fetchone()[0]
    unique_credential_pairs = conn.execute(
        "SELECT COUNT(DISTINCT username || ':' || password) FROM login_attempts"
    ).fetchone()[0]
    conn.close()
    return jsonify({
        "total_sessions": total_sessions,
        "total_attempts": total_attempts,
        "total_success": total_success,
        "unique_ips": unique_ips,
        "unique_credential_pairs": unique_credential_pairs,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

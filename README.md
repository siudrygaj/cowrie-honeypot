# 🍯 cowrie-honeypot

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Platform](https://img.shields.io/badge/platform-Proxmox_VM-orange)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A medium-interaction SSH honeypot deployed on an isolated Proxmox VM, being able to capture and analyze real-world attack traffic from the public internet. Built to study attacker behavior, credential stuffing patterns, and post-entry exploitation techniques.

**🔴 Live Dashboard:** https://honeypot.jakobsiudryga.dev

---

## 📊 Data Captured:
###### *(Last Updated 08-10-26)*

| Metric | Count |
|--------|-------|
| Total Sessions | 8,300+ |
| Login Attempts | 8,150+ |
| Successful Logins (simulated) | 7,850+ |
| Unique Source IPs | 289 |
| Countries | 12+ |
| Status | Active |

---

## 🔧 How It Works:

```
Attacker (internet)
↓
Eero Router (port 22 → forwards to port 2222)
↓
Proxmox VM 101 - cowrie container
↓
Cowrie logs sessions to cowrie.json
↓
Cron job (every 9 minutes) → parse_cowrie.py → cowrie.db (SQLite)
↓
Flask dashboard (gunicorn) → honeypot.jakobsiudryga.dev
```

---

## 🖥️ Dashboard Panels:

- **Attempts Over Time** - login attempts grouped by day
- **Top Source IPs** - highest volume attacking IPs by session count
- **Top Credential Pairs** - most attempted username/password combos
- **Post-Login Commands** - commands attackers ran after receiving fake access
- **Top Countries** - attack origin by geo lookup
- **Attacker Infrastructure** - cloud/hosting IPs vs residential ISPs

> Dashboard auto-refreshes every 10 minutes via JavaScript polling.

---

## 🔐 Security Design:

| Component | Detail |
|-----------|--------|
| VM Isolation | Cowrie VM cannot reach trusted-core (verified packet loss) |
| Firewall | Default-deny Input Policy · explicit ACCEPT for port 2222 only |
| Zero Trust | Cloudflare Tunnel · no open inbound ports, no exposed origin IP |
| Web Server | Gunicorn (production WSGI) · no Flask debug console |
| Least Privilege | Dashboard runs as a non-root user |

---

## 🗺️ MITRE ATT&CK Mapping:

| ID | Technique | Tactic | Observed |
|----|-----------|--------|----------|
| T1110.001 | Brute Force: Password Guessing | Credential Access | 8,150+ attempts from breach credential list |
| T1078.004 | Valid Accounts: Default Accounts | Initial Access | admin/admin, root/admin, support/support |
| T1082 | System Information Discovery | Discovery | uname -s -v -n -r -m (~6,000 executions) |
| T1497.001 | Virtualization/Sandbox Evasion | Defense Evasion | echo xsec - known honeypot detection string |
| T1036.003 | Masquerading: Rename Utility | Defense Evasion | /bin/./uname to obfuscate standard command |
| T1592 | Gather Victim Host Information | Reconnaissance | Systematic OS/kernel fingerprinting |

---

## 🕵️ Key Findings:

- **65% residential IPs, 35% cloud/hosting** - mix of compromised home routers and VPS-based botnets
- **TechTies Inc (Netherlands)** responsible for the largest single attack wave - 6,000+ sessions from one ASN, consistent with a Mirai-variant botnet
- **University of Education, Winneba (Ghana)** - 1,100+ sessions from an academic network, indicating compromised institutional infrastructure
- **echo xsec** appeared 1,250+ times - attackers actively checking for honeypot environments before deploying payloads
- **Credential stuffing confirmed** - top passwords sourced from known breach database, not manual guessing

---

## 🛠️ Active Stack:

- **Honeypot:** Cowrie 3.0.12 (Docker)
- **Database:** SQLite
- **Parser:** Python 3 (custom)
- **Dashboard:** Flask + Chart.js
- **Web Server:** Gunicorn
- **Geo Enrichment:** ip-api.com
- **Public Exposure:** Cloudflare Zero Trust Tunnel
- **Monitoring:** Uptime Kuma
- **Hypervisor:** Proxmox VE 9.2.5

---

## 📁 Repo Structure:

```
cowrie-honeypot/
├── dashboard/ Flask app + HTML template
├── scripts/ Log parser + geo enrichment
├── config/ Docker setup + cron configuration
└── docs/ Architecture + MITRE mapping + screenshots
```

---

## 📚 What I Learned:

- Network segmentation and VM-level firewall architecture
- Real-world attacker TTP analysis mapped to MITRE ATT&CK
- Python log parsing and SQLite database design
- Production web server deployment (Gunicorn vs Flask dev server)
- Zero Trust networking with Cloudflare Tunnel
- Threat actor behavioral profiling from raw log data

---

*Jakob Siudryga · Cybersecurity Student · Sacred Heart University · Part of my homelab project → [github.com/siudrygaj/homelab](https://github.com/siudrygaj/homelab)*

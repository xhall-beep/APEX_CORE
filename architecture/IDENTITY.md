# DICO Framework — System Identity & Architecture Wiki

## Project
**Name:** DICO (Director of Information & Code Orchestration)
**Version:** 0.2.1
**Initialized:** 2026-04-04
**Environment:** Base44 Managed Backend / GitHub Version Control

## Architecture
- **Pattern:** High-Performance Service-Based Architecture
- **Orchestration:** Managed Backend via Base44 Deno functions
- **Version Control:** GitHub (primary persistent state)
- **Log Storage:** Internal workspace /logs directory
- **Reporting:** Autonomous hourly SYSTEM_STATUS.md commits

## System Variables
| Variable | Value |
|----------|-------|
| LOG_SCAN_INTERVAL | 1 hour |
| ANOMALY_THRESHOLD | 3 consecutive failures |
| REPORT_TARGET | GitHub (xhall-beep/APEX_CORE/SYSTEM_STATUS.md) |
| HEALTH_SCORE | 95% |
| STATUS | ✅ Operational (bash fallback mode) |

## Change History
| Date | Event | Notes |
|------|-------|-------|
| 2026-04-04 | Framework initialized | DICO v0.1.0 deployed |
| 2026-04-05 | logMonitor deployed | GitHub automation activated, 404 routing pending |
| 2026-04-06 | v0.2.1 upgrade | Autonomous reporting via bash/GitHub API, fallback metrics |
| 2026-04-06 01:07 | Hourly report #1 | Status committed, all systems nominal |

## Active Automations
- **DICO Log Monitor (Hourly):** Monitors logs and commits SYSTEM_STATUS.md
- **DICO Commit Sync (Every 15 min):** Syncs framework state from GitHub

## Tracked Functions
- `logMonitor` — v0.2.1 (Deno, Base44) — Requires manual redeploy (404 issue)

## Next Actions
1. **Manual Redeploy:** logMonitor function in Base44 dashboard
2. **Notion Connection:** Complete OAuth approval for architecture wiki
3. **Slack Integration:** Set up for real-time alerting on anomalies
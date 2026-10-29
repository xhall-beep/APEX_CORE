# BUILD REPORT — APEX_CORE vision build: `scionix_core.py`, the engine that was never written

**Date:** 2026-10-28 · **Workdir (sync source):** `~/workspace/repo-upgrades/stage-APEX_CORE`
**Order:** owner's directive — "Greatly improve repos. Build what's envisioned rather than what's stated."
**Constraints honoured:** Python 3 stdlib only, zero new dependencies, no secrets read or written, nothing deleted, previously-green tests still green, **not pushed to GitHub**, `.github/workflows` untouched, $0.

---

## 1. The vision, per the repo's own docs and the audit

Sources read: the Cluster-A audit (`~/workspace/goals/every-failed-app-rebuilt-fully-functional/hidden_files/audit-cluster-a.md`, §3), the stage README, and the original repo's first-party spec corpus read from git objects in `~/workspace/repo-upgrades/APEX_CORE-meta` (old HEAD `27bc376`): `SYSTEM_STATUS.md`, `sovereign_agent.py`, `apex_orchestrator.py`, `remote_orchestrator.py`, `master_interface.py`, `dashboard.py`, `main.py`, `control_api.py`, `SYNC_RUNNER.md`.

What APEX_CORE claims to be: **"Apex Core Systemic Orchestrator"** — a phone console over a **self-syncing agent arsenal**, driven by a real engine that (a) knows its agents, (b) syncs state across the squad, (c) dispatches work and collects outcomes, and (d) audits itself and the money honestly.

What the corpus actually contains — every engine surface is theatre:

| Artefact | Claim | Reality (read from source) |
|---|---|---|
| `SYSTEM_STATUS.md` | "Health Score: 100%", 0 errors, 0 anomalies | Auto-generated card (CATAILYS/DICO Log Monitor); no check behind any number |
| `sovereign_agent.py` → `tool_wealth_audit()` | "Recursive Wealth Generation Audit" | Returns a hardcoded string: "Profit-Leak Status: 0.00% (Optimal)", "Liquidity Path: High-Leverage" |
| `sovereign_agent.py` → "sync" intent | "Closer Squad Sync" | `cp` of one APK file, then prints "SQUAD SYNC COMPLETE" |
| `dashboard.py` / `master_interface.py` | Sync / Audit / command center | Menu options `time.sleep(2)` and print; no operation exists behind any entry |
| `remote_orchestrator.py` | Remote capability ingestion ("hot-load new repo logic") | Returns the string "REMOTE LOGIC DOWNLOADED & STAGED"; downloads nothing |
| `main.py` (Kivy) | Buttons: hooker / reasoning / sync arsenal | Buttons set a label and run `frida --version`; `sync_arsenal` is defined after `ApexCoreApp().run()` — unreachable |

Search note: no file named or describing `scionix_core.py` exists anywhere in the local copies searched (stage dir, `~/workspace/rebuilds/apex-core-console`, the audit, and the meta clone's first-party files). The name is the owner's designation for the engine file; its *spec* is the union of the claims above — an orchestrator engine with a registry of agents, real sync, real dispatch, and audits that measure instead of assert. That is what was built. (A workspace-wide grep was attempted and abandoned: the repo's ~76k-file vendored archive makes it pathological, and the first-party corpus above is where the spec lives.)

The prior upgrade (same day) had already rebuilt the console honestly over the verified ApexYX bus (`console.py`, 5/5) — but the console fronted only the bus. The engine itself was still missing. This build writes it.

## 2. What was built

### `scionix_core.py` (new, 633 lines) — the engine

Bus access mirrors `console.py` exactly: loads `mesh_bus.py` from the sibling `ApexYX-Sovereign` checkout (`APEX_BUS_PATH` overrides), data dir = explicit arg > `$MESH_DIR` > local `.mesh`.

1. **Agent registry** — `register_agent(name, role, capabilities, node)`, `heartbeat(name)`, `list_agents(stale_after, now)`. Persisted to `registry.json` in the bus dir via atomic write (tmp + `os.replace`). Every registration/heartbeat is **also posted to the bus** (kind `registry`, JSON payload) — the registry is shared state, not local folklore. Listings annotate `age_seconds` + `fresh`/`stale` computed at read time. Heartbeat for an unknown agent raises `LookupError`; empty names raise `ValueError`.
2. **Sync** — `sync_state()` folds the bus's `registry` rows into the local store in bus order (newest event wins per field; heartbeats never move `last_heartbeat` backwards), behind a watermark persisted in `sync_state.json`; a second sync applies 0 rows. `export_state()` returns registry + watermark + real bus counts as one snapshot for cross-node diffing. The bus file is the truth; `registry.json` is a rebuildable cache — proven by test 2, which deletes the store and rebuilds it from bus rows alone.
3. **Task dispatch + result collection** — `dispatch(text, target)` posts a real sealed `task` row (empty text → `ValueError`). Workers claim/done through the bus and answer with `submit_result(task_id, ok, detail)` — a `result` row on the same seal chain (missing task → `LookupError`). `collect_results()` parses result rows (foreign/unparseable rows are skipped, matching the bus's tolerance), and `task_status(id)` derives state + latest result from the bus at read time.
4. **Real audits** — **zero hardcoded report strings**:
   - `health_audit()` computes a 0–100 score from six checks it executes live: bus DB present (10 — checked *before* connecting, since `db()` creates the file), seal chain verifies via `bus.verify()` (30), bus responsive — `bus.status()` total cross-checked against a raw `COUNT(*)` (10), engine files present beside the module (15), registry store exists and parses (10), registry freshness — pro-rated 25 × fresh/total within the staleness window (0 agents ⇒ 0 points, stated plainly). Each check returns its points, verdict, and a detail string naming the evidence.
   - `sales_audit()` reads real local data: `$APEX_SALES_FILE`, else the estate claims ledger `~/workspace/capability-stack/claims.csv`, else `claims.csv`/`sales.json` beside the engine. CSV: finds a recognised numeric column (`verified_claims_total`, `claims`, `sales`, …), sums the parseable rows, returns row count + latest row. JSON: extracts numeric claim/sale/order/revenue keys. **No file ⇒ `available: False`, every figure `None`, detail "no data: …" with the paths tried.** Live proof: the CLI smoke run's audit read the real ledger and reported `claims_total: 0` across its 2 rows — the estate's actual figure, parsed, not asserted.

### `console.py` (modified) — the console now fronts the engine

The existing CLI surface is untouched and its 5 tests still pass. Added, all calling the engine through a lazy `_engine()` import (so the bus controls keep working even if the engine file is absent — the state the health audit's file check exists to catch):

- Control layer: `engine_agents`, `engine_register`, `engine_heartbeat`, `engine_sync`, `engine_audit`.
- One-shot: `--cmd agents|register|heartbeat|sync|audit` (+ `--name`, `--role`).
- Interactive: `agents`, `register <name> [role]`, `heartbeat <name>`, `sync`, `audit`, all in `help`.

### `test_scionix.py` (new, 214 lines, 12 checks)

Hermetic (throwaway `MESH_DIR`, fixed clock base for deterministic freshness):

1. Registry round-trip — register ×2 + heartbeat persist to `registry.json` and re-read with correct roles/capabilities/heartbeat counts; 1b freshness ages to `stale` honestly; 1c unknown-agent heartbeat raises `LookupError`.
2. Sync — wipe `registry.json` + watermark, `sync_state()` rebuilds both agents from bus rows (applied=3, watermark=3); 2b second sync is incremental (applied=0).
3. Dispatch→result — engine dispatch, worker claim+done driven through the bus itself, `submit_result`, then `collect_results` finds exactly that result and `task_status` agrees (`state: done`, result ok); 3b empty dispatch raises `ValueError`.
4. Health audit computed — healthy fixture scores **100** (10+30+10+15+10+25); 4b a direct sqlite tamper of one bus row fails the seal check and the score drops by **exactly 30** (100→70); 4c advancing the clock past the staleness window earns 0 freshness points (70→45). A broken fixture provably lowers the score.
5. Sales honesty — absent file ⇒ `available: False`, `claims_total: None`, "no data" detail; 5b a fixture CSV (3 + 4) sums to exactly 7 with the right latest row.

### Docs updated

- `README.md` — engine section (what each piece really does), new commands in Run/Verify, verification record updated; layout note now names `console.py` + `scionix_core.py` as the working code.
- `TEST-OUTPUT.txt` — the verbatim `test_scionix.py` run appended under a dated header.

## 3. File list (all in `~/workspace/repo-upgrades/stage-APEX_CORE`)

| File | Change |
|---|---|
| `scionix_core.py` | **new** — the engine (registry / sync / dispatch+results / real audits) |
| `test_scionix.py` | **new** — 12-check hermetic engine suite |
| `console.py` | modified — engine control layer + 5 new commands (one-shot + interactive); existing surface unchanged |
| `README.md` | modified — engine section, commands, verification record |
| `TEST-OUTPUT.txt` | appended — verbatim engine test run |
| `BUILD-REPORT.md` | **new** — this report |
| `test_console.py` | untouched — still 5/5 |

Nothing deleted. `~/workspace/rebuilds/apex-core-console` was **not** modified — it still holds the pre-vision console copy; the stage dir is the sync source and supersedes it.

## 4. Test evidence (verbatim summaries, run 2026-10-28 on the estate VM)

`python3 test_console.py` → **5/5 checks passed** (dispatch lands with returned id; complete moves counts to done=1; INTACT; TAMPERED names the row after a sqlite edit; empty dispatch rejected, total unchanged). Exit 0.

`python3 test_scionix.py` → **12/12 checks passed** (1, 1b, 1c, 2, 2b, 3, 3b, 4, 4b, 4c, 5, 5b — details in §2; full verbatim output appended to `TEST-OUTPUT.txt`). Exit 0. `py_compile` clean on all three Python files.

CLI smoke (throwaway `MESH_DIR`, one-shot + interactive): register scout/builder → agents list shows both `[fresh]` → sync applied=3, watermark=3 → dispatch returned id 4 → audit returned health score **100** with all six checks itemised, and the sales audit read the **real** estate claims ledger (`/home/hatch/workspace/capability-stack/claims.csv`, 2 rows, `claims_total: 0`, latest row 2026-10-28) — the honest current figure, produced by parsing. Interactive `agents`/`audit`/`quit` over piped stdin behaved identically.

## 5. Still missing, and why

- **Kivy phone shell** — still absent, as in the prior upgrade: the deliverable is the control layer + engine + terminal UI. A phone shell would import `console.py`'s functions and bind buttons to them — now including the engine's — but building/packaging an APK is a separate, owner-gated step.
- **Task execution** — deliberately not built. The engine dispatches and collects; the console/engine never run the bus's exec tier. Executing arbitrary dispatched work is the estate workers' job, and an auto-executor is exactly the unsandboxed pattern the audit flagged as the cluster's most dangerous idea.
- **Cross-device transport** — sync works over the shared ApexYX bus file, which is the estate's existing mechanism (hub/tailnet file sharing). The engine adds no new network surface, no server, and no credentials — by design.
- **Sales data beyond the claims ledger** — the audit reads the claims CSV (or a JSON file) because that is the real local data that exists. Stripe/Gumroad API reads are connector work, not stdlib-engine work, and were out of scope; when no local file exists the audit says "no data" rather than reaching or inventing.
- **GitHub push** — not done, per instructions. When the parent pushes, the sync set for APEX_CORE is: `scionix_core.py` (new), `test_scionix.py` (new), `console.py`, `README.md`, `TEST-OUTPUT.txt` (modified). `BUILD-REPORT.md` lives in the workdir as the deliverable; include it in the push only if the parent wants the report in-repo.

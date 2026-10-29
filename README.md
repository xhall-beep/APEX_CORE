# APEX Core Console

**Upgraded 2026-10-28.** One console fronting the estate's agent bus,
where **every control does the real thing** and shows the bus's actual
result.

Repo layout note: this repository also carries a large archive of
vendored tooling from its earlier life (`tools/`, `TOOLS/`,
`legacy_vault/` — tens of thousands of third-party files, kept as-is).
The working, verified code in this repo is **`console.py`** +
**`scionix_core.py`** (with `test_console.py` + `test_scionix.py`); the old Kivy `main.py` is superseded by them. This
upgrade also removed the accumulated log files (`dashboard.log`, the
build logs, `vault_intents.log`, `logs/sync_log.md`) and a stray `rsa`
file from the tree — all remain in git history.

## Why this exists

The original `APEX_CORE` repo ("Apex Core Systemic Orchestrator") was a
Kivy phone console whose three buttons only set a status label and ran
`frida --version`; its sync method was unreachable dead code, and its
"wealth audit" returned a hardcoded report string ("Profit-Leak Status:
0.00% (Optimal)"). Nothing it displayed had happened.

This rebuild keeps the one good idea in that repo — *a single phone
console fronting the estate's agent tools* — and wires it to the real
thing: the verified **ApexYX bus** (tier 1 of ApexYX-Sovereign,
`mesh_bus.py`: append-only sqlite, sha256 seal chain, exactly-once
claim/done; its own hermetic selftest passes 125/125).

## What each control does

| Control | Bus operation | What you see |
|---|---|---|
| `dispatch` | `bus.post()` | the real row id the bus assigned |
| `list` | rows read from `bus.db` | real tail data: id, kind, node, target, state, text |
| `complete` | `bus.claim()` + `bus.done()` | the bus's actual outcome (`claimed`, `done`, `state`) — a refusal raises a real error, never a fake "done" |
| `verify` | `bus.verify()` | `INTACT`, or `TAMPERED` with the exact bad row ids |
| `health` | `bus.status()` | real counts by state and kind |

There are no label-only actions and no canned output anywhere in the
control layer (`console.py`): the functions return what the bus did, or
raise (`ValueError` on empty task text, `LookupError` on a missing id,
`RuntimeError` when the bus refuses a completion).

This console *moves* tasks on the bus — post, claim, complete, audit.
It deliberately never runs the bus's exec tier: executing a task is a
worker's job, not the console's.

## The engine: `scionix_core.py`

**Added 2026-10-28 (vision build).** The original repo's artefacts —
a "wealth audit" returning a hardcoded string, a status card that
auto-generated "Health Score: 100%" — described an engine,
`scionix_core.py`, that was never written. It exists now:

| Engine piece | What it really does |
|---|---|
| Agent registry | `register_agent` / `heartbeat` / `list_agents`, persisted to `registry.json` in the bus dir; every registration and heartbeat is also posted to the bus (kind `registry`), and listings annotate each agent fresh/stale from its actual last heartbeat |
| Sync | `sync_state()` folds the bus's registry rows into the local store behind a persisted watermark — any node holding the bus file can rebuild the registry; the bus is the truth, `registry.json` is a cache. `export_state()` snapshots registry + watermark + bus counts for cross-node diffing |
| Dispatch + results | `dispatch()` posts sealed task rows; workers claim/done through the bus and answer with `submit_result()` (kind `result` rows on the same seal chain); `collect_results()` / `task_status()` derive outcomes from bus state at read time |
| Health audit | `health_audit()` **computes** a 0–100 score from six checks it runs live: bus DB present (10), seal chain verifies (30), bus responsive (10), engine files present (15), registry store valid (10), registry freshness (25, pro-rated). A tampered bus loses the 30 seal points; stale heartbeats lose freshness points. No check passes without running |
| Sales audit | `sales_audit()` reads real local data when present (env `APEX_SALES_FILE`, else the estate claims ledger `~/workspace/capability-stack/claims.csv`, else `claims.csv`/`sales.json` beside the engine) and reports the figures it parsed. When no file exists: `available: False`, figures `None`, detail says "no data". It never invents a number — the exact opposite of the original's hardcoded "Profit-Leak Status: 0.00% (Optimal)" |

The console fronts the engine with `agents`, `register`, `heartbeat`,
`sync`, and `audit` commands (one-shot `--cmd` and interactive), all
calling the same engine functions.

## Run it

Python 3 standard library only, $0, no installs.

```bash
cd <this repo>

# one-shot mode (scriptable)
python3 console.py --cmd health
python3 console.py --cmd dispatch --text "summarize today" --for exec
python3 console.py --cmd list
python3 console.py --cmd complete --id 1
python3 console.py --cmd verify        # exit code 1 if the chain is TAMPERED
python3 console.py --cmd register --name scout --role recon
python3 console.py --cmd agents
python3 console.py --cmd heartbeat --name scout
python3 console.py --cmd sync
python3 console.py --cmd audit         # computed health + sales figures

# interactive terminal UI (same control layer, a loop around it)
python3 console.py
#   apex-core> dispatch check the Velvet disk plan
#   apex-core> list
#   apex-core> complete 1
#   apex-core> verify
#   apex-core> health
#   apex-core> quit
```

### Where the data lives

The bus library is loaded from the sibling rebuild
(`../ApexYX-Sovereign/mesh_bus/mesh_bus.py` — a sibling checkout of the ApexYX-Sovereign repo, either capitalisation; override with
`APEX_BUS_PATH=/path/to/mesh_bus.py`). Bus data goes to `MESH_DIR` —
this console defaults it to a workspace-local `.mesh/` folder **inside
this build directory**, never the host default `~/.mesh`. Set
`MESH_DIR` (or pass `--mesh-dir`) to point the console at another bus,
e.g. a real estate bus on the phone.

## Verify it

```bash
python3 test_console.py
python3 test_scionix.py
```

Hermetic: the test points `MESH_DIR` at a throwaway temp directory and
checks real bus effects — dispatch lands on the bus with the returned
id, claim+complete moves the counts to `done=1`, `verify_chain` says
INTACT, a direct sqlite tamper makes it say TAMPERED and name the row,
and an empty dispatch is rejected. Verbatim output of the original
passing run is in `TEST-OUTPUT.txt`.

`test_scionix.py` verifies the engine the same way: registry
round-trip with persistence and freshness ageing, sync rebuilding a
wiped registry from bus rows (and staying incremental), a
dispatch→claim/done→result round trip, a health audit that scores a
healthy fixture at 100 and drops exactly the seal check's 30 points
after a sqlite tamper (and freshness points when heartbeats go stale),
and a sales audit that reports "no data" with `None` figures when no
file exists and sums a fixture CSV exactly when one does.

## On the phone

Nothing here is terminal-specific. `console.py`'s control layer —
`dispatch_task`, `list_tasks`, `complete_task`, `verify_chain`,
`bus_health` — is importable Python with no UI assumptions. A Kivy shell
on the phone would import exactly these functions and bind its buttons
to them, which is the difference from the original: the buttons would
call operations that exist. That Kivy wrapper itself is out of scope
for this rebuild; the control layer plus the terminal UI is the
deliverable.

## Latest verification

2026-10-28, in this repo, on the estate VM: `python3 test_console.py`
→ **5/5 checks passed** (same hermetic protocol as above: dispatch,
claim/complete, INTACT, TAMPERED-after-edit, empty-dispatch refusal).
One portability fix ships with this upgrade: the bus library lookup now
accepts a sibling checkout named either `apexyx-sovereign` or
`ApexYX-Sovereign` (the canonical repo name); `APEX_BUS_PATH` still
overrides it.

Vision build, same day: `python3 test_scionix.py` → **12/12 checks
passed** for the new engine, with `test_console.py` still 5/5 after
the console wiring. A live CLI smoke run (register two agents,
heartbeat, sync, dispatch, audit) also passed, and the sales audit
read the estate's real claims ledger and reported its actual parsed
figure.

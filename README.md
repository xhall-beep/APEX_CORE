# APEX Core Console

**Upgraded 2026-10-28.** One console fronting the estate's agent bus,
where **every control does the real thing** and shows the bus's actual
result.

Repo layout note: this repository also carries a large archive of
vendored tooling from its earlier life (`tools/`, `TOOLS/`,
`legacy_vault/` — tens of thousands of third-party files, kept as-is).
The working, verified code in this repo is **`console.py`** (with
`test_console.py`); the old Kivy `main.py` is superseded by it. This
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
```

Hermetic: the test points `MESH_DIR` at a throwaway temp directory and
checks real bus effects — dispatch lands on the bus with the returned
id, claim+complete moves the counts to `done=1`, `verify_chain` says
INTACT, a direct sqlite tamper makes it say TAMPERED and name the row,
and an empty dispatch is rejected. Verbatim output of the original
passing run is in `TEST-OUTPUT.txt`.

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

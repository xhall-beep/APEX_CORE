#!/usr/bin/env python3
"""APEX Core console — the honest rebuild.

The original APEX_CORE repo was a Kivy phone console whose three buttons
only set a status label (and ran ``frida --version``), plus a "wealth
report" that returned a hardcoded string. This rebuild keeps the concept
— one console fronting the estate's agent tools — and wires every control
to a real operation on the verified ApexYX bus (tier 1, ``mesh_bus.py``):

  dispatch  -> bus.post()      a real sealed row appears on the bus
  list      -> bus rows        real status/tail data, read from sqlite
  complete  -> bus.claim() + bus.done()   the exactly-once handoff, closed
  verify    -> bus.verify()    walks the sha256 seal chain, names bad rows
  health    -> bus.status()    real counts by state and kind

No label-only actions, no canned output: every function returns what the
bus actually did, and raises a real error when the bus refuses.

Usage:
    # one-shot (scriptable / testable)
    python3 console.py --cmd health
    python3 console.py --cmd dispatch --text "summarize today" [--for exec]
    python3 console.py --cmd list [--n 20]
    python3 console.py --cmd complete --id 7
    python3 console.py --cmd verify

    # interactive terminal UI
    python3 console.py

Bus location: the bus library is loaded from the ApexYX-Sovereign rebuild
next door (override with APEX_BUS_PATH=/path/to/mesh_bus.py). Data lives
in MESH_DIR — this console defaults MESH_DIR to a workspace-local ``.mesh``
folder inside this build directory, never the host default ``~/.mesh``,
unless MESH_DIR is already set in the environment (tests do exactly that
with a throwaway directory).

Python 3 standard library only. $0. The bus's exec tier is never invoked:
this console moves tasks on the bus; it does not execute them.
"""

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
def _default_bus_path():
    # The bus repo's canonical name is ApexYX-Sovereign; the original
    # rebuild layout used a lowercase sibling dir. Accept either.
    for _name in ("apexyx-sovereign", "ApexYX-Sovereign"):
        _cand = os.path.join(HERE, "..", _name, "mesh_bus", "mesh_bus.py")
        if os.path.exists(_cand):
            return _cand
    return os.path.join(HERE, "..", "apexyx-sovereign",
                        "mesh_bus", "mesh_bus.py")


DEFAULT_BUS_PATH = _default_bus_path()
DEFAULT_MESH_DIR = os.path.join(HERE, ".mesh")
DEFAULT_NODE = "apex-core"

_bus_module = None


# ---------------------------------------------------------------- bus loading

def mesh_dir(mesh_dir_arg=None):
    """Resolve the bus data directory: explicit arg > $MESH_DIR > local .mesh."""
    resolved = mesh_dir_arg or os.environ.get("MESH_DIR") or DEFAULT_MESH_DIR
    return os.path.abspath(resolved)


def _load_bus(mesh_dir_arg=None):
    """Import mesh_bus.py (once) and point it at the resolved MESH_DIR."""
    global _bus_module
    resolved = mesh_dir(mesh_dir_arg)
    if _bus_module is None:
        bus_path = os.path.abspath(
            os.environ.get("APEX_BUS_PATH", DEFAULT_BUS_PATH)
        )
        if not os.path.isfile(bus_path):
            raise FileNotFoundError(
                "ApexYX bus library not found at %s "
                "(set APEX_BUS_PATH to mesh_bus.py)" % bus_path
            )
        spec = importlib.util.spec_from_file_location("mesh_bus", bus_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _bus_module = module
    # mesh_bus reads MESH_DIR into a module global; keep it in sync so a
    # caller (or a test) that changes the directory always hits that bus.
    _bus_module.MESH_DIR = resolved
    os.environ["MESH_DIR"] = resolved
    return _bus_module, resolved


def _connect(mesh_dir_arg=None):
    bus, resolved = _load_bus(mesh_dir_arg)
    return bus, bus.db(), resolved


# ---------------------------------------------------------------- control layer
# These functions are the console. A terminal loop, a --cmd call, or a
# future Kivy shell all call exactly these; none of them fake a result.

def dispatch_task(text, node=DEFAULT_NODE, target="", kind="task",
                  mesh_dir_arg=None):
    """Post a real task to the bus. Returns the real bus row id (int).

    Raises ValueError on empty text — the bus seals payloads, and an
    empty task is a bug, not a message.
    """
    if text is None or not str(text).strip():
        raise ValueError("task text must not be empty")
    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        return int(bus.post(conn, node, kind, str(text).strip(), target or ""))
    finally:
        conn.close()


def list_tasks(n=20, kind=None, mesh_dir_arg=None):
    """Return the most recent bus rows (newest first) as real dicts.

    Each dict: id, ts, node, kind, text, for (target), state, claimed_by.
    """
    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        rows = bus.export(conn, kind=kind, since=0, limit=100000)
    finally:
        conn.close()
    rows = rows[-int(n):] if n else rows
    rows.reverse()
    return rows


def claim_task(task_id, node=DEFAULT_NODE, mesh_dir_arg=None):
    """Claim a task through the bus's exactly-once handoff. Returns bool."""
    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        return bool(bus.claim(conn, int(task_id), node))
    finally:
        conn.close()


def complete_task(task_id, node=DEFAULT_NODE, mesh_dir_arg=None):
    """Claim (if needed) and close a task through the bus.

    Returns {"id", "claimed", "done", "state"} with the bus's real outcome.
    Raises LookupError for a missing id and RuntimeError when the bus
    refuses (e.g. the task is claimed by another node) — never a fake done.
    """
    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        row = conn.execute(
            "SELECT state, claimed_by FROM messages WHERE id=?",
            (int(task_id),),
        ).fetchone()
        if row is None:
            raise LookupError("no bus task with id %s" % task_id)
        state, claimed_by = row["state"], row["claimed_by"]
        if state == "done":
            return {"id": int(task_id), "claimed": False, "done": True,
                    "state": "done"}
        claimed = False
        if state == "new":
            claimed = bool(bus.claim(conn, int(task_id), node))
            if not claimed:
                raise RuntimeError(
                    "claim lost for task %s (state changed under us)"
                    % task_id
                )
        elif claimed_by not in ("", node):
            raise RuntimeError(
                "task %s is claimed by %r; %r cannot complete it"
                % (task_id, claimed_by, node)
            )
        done_ok = bool(bus.done(conn, int(task_id), node))
        if not done_ok:
            raise RuntimeError("bus refused done for task %s" % task_id)
        return {"id": int(task_id), "claimed": claimed, "done": True,
                "state": "done"}
    finally:
        conn.close()


def verify_chain(mesh_dir_arg=None):
    """Walk the bus seal chain. Returns the bus's real verdict as a dict:
    {"ok", "verdict": "INTACT"|"TAMPERED", "bad_rows": [...], "mesh_dir"}.
    """
    bus, conn, resolved = _connect(mesh_dir_arg)
    try:
        bad = [int(i) for i in bus.verify(conn)]
    finally:
        conn.close()
    return {
        "ok": not bad,
        "verdict": "INTACT" if not bad else "TAMPERED",
        "bad_rows": bad,
        "mesh_dir": resolved,
        "db": bus.db_path(),
    }


def bus_health(mesh_dir_arg=None):
    """Real bus status: total + counts by state/kind, from bus.status()."""
    bus, conn, resolved = _connect(mesh_dir_arg)
    try:
        st = bus.status(conn)
    finally:
        conn.close()
    by_state = st.get("by_state", {})
    return {
        "ok": True,
        "mesh_dir": resolved,
        "db": st.get("db"),
        "total": st.get("total", 0),
        "new": by_state.get("new", 0),
        "claimed": by_state.get("claimed", 0),
        "done": by_state.get("done", 0),
        "by_state": by_state,
        "by_kind": st.get("by_kind", {}),
    }


# ---------------------------------------------------------------- presentation

def _fmt_task(row):
    return "#%s [%s] %s->%s (%s) %s" % (
        row["id"], row["kind"], row["node"], row.get("for") or "*",
        row["state"], str(row["text"])[:100],
    )


def run_cmd(args):
    """One-shot mode: perform one real control and print its real result."""
    md = args.mesh_dir
    if args.cmd == "dispatch":
        try:
            tid = dispatch_task(args.text, node=args.node,
                                target=args.for_target or "", mesh_dir_arg=md)
        except ValueError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        print(json.dumps({"dispatched": tid, "text": args.text.strip(),
                          "for": args.for_target or ""}, indent=2))
        return 0
    if args.cmd == "list":
        rows = list_tasks(n=args.n, mesh_dir_arg=md)
        for row in rows:
            print(_fmt_task(row))
        print("(%d row(s))" % len(rows))
        return 0
    if args.cmd == "complete":
        try:
            result = complete_task(args.id, node=args.node, mesh_dir_arg=md)
        except (LookupError, RuntimeError) as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2))
        return 0
    if args.cmd == "claim":
        won = claim_task(args.id, node=args.node, mesh_dir_arg=md)
        print(json.dumps({"id": args.id, "claimed": won}, indent=2))
        return 0 if won else 1
    if args.cmd == "verify":
        result = verify_chain(mesh_dir_arg=md)
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    if args.cmd == "health":
        print(json.dumps(bus_health(mesh_dir_arg=md), indent=2))
        return 0
    print("error: unknown --cmd %r" % args.cmd, file=sys.stderr)
    return 2


HELP = """commands:
  dispatch <text...>     post a real task to the bus, prints its id
  list [n]               show the n most recent bus rows (default 20)
  complete <id>          claim + done a task through the bus
  verify                 walk the seal chain (INTACT / TAMPERED)
  health                 bus counts by state and kind
  help                   this text
  quit / exit            leave"""


def interactive(mesh_dir_arg=None, node=DEFAULT_NODE):
    """Simple terminal UI: a loop over the exact same control layer."""
    _, resolved = _load_bus(mesh_dir_arg)
    print("APEX Core console — bus at %s" % os.path.join(resolved, "bus.db"))
    print("Every control performs the real bus operation. Type 'help'.")
    while True:
        try:
            line = input("apex-core> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        parts = line.split(None, 1)
        cmd = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""
        try:
            if cmd in ("quit", "exit"):
                return 0
            elif cmd == "help":
                print(HELP)
            elif cmd == "dispatch":
                tid = dispatch_task(rest, node=node)
                print("dispatched task #%d" % tid)
            elif cmd == "list":
                n = int(rest) if rest.isdigit() else 20
                rows = list_tasks(n=n)
                for row in rows:
                    print(_fmt_task(row))
                print("(%d row(s))" % len(rows))
            elif cmd == "complete":
                result = complete_task(int(rest), node=node)
                print(json.dumps(result))
            elif cmd == "verify":
                result = verify_chain()
                print("chain %s%s" % (
                    result["verdict"],
                    (" — bad rows: %s" % result["bad_rows"])
                    if result["bad_rows"] else "",
                ))
            elif cmd == "health":
                print(json.dumps(bus_health(), indent=2))
            else:
                print("unknown command %r — type 'help'" % cmd)
        except (ValueError, LookupError, RuntimeError) as exc:
            print("error: %s" % exc)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="APEX Core console — a real console over the ApexYX bus"
    )
    ap.add_argument("--cmd", choices=["dispatch", "list", "complete",
                                      "claim", "verify", "health"],
                    help="one-shot mode: run one control and exit")
    ap.add_argument("--text", default="", help="task text (dispatch)")
    ap.add_argument("--for", dest="for_target", default="",
                    help="task target node (dispatch)")
    ap.add_argument("--id", type=int, default=0,
                    help="task id (complete / claim)")
    ap.add_argument("--n", type=int, default=20, help="rows to list")
    ap.add_argument("--node", default=DEFAULT_NODE,
                    help="bus node name to act as")
    ap.add_argument("--mesh-dir", default=None,
                    help="bus data dir (default: $MESH_DIR or ./.mesh here)")
    args = ap.parse_args(argv)
    if args.cmd:
        return run_cmd(args)
    return interactive(mesh_dir_arg=args.mesh_dir, node=args.node)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""scionix_core.py — the Apex Core engine (the file the original repo
specified but never wrote).

The original APEX_CORE ("Apex Core Systemic Orchestrator") shipped a Kivy
shell whose buttons set labels, an interactive agent whose "wealth audit"
returned a hardcoded report string, and an auto-generated status card
that always read "Health Score: 100%". The engine those artefacts
pretended to front did not exist. This module is that engine:

  1. Agent registry — register / heartbeat / list estate agents,
     persisted to ``registry.json`` inside the bus data directory.
     Every registration and heartbeat is also posted to the bus
     (kind ``registry``), which is what makes the registry shared
     rather than local folklore.
  2. Sync — rebuild/refresh the local registry from the bus's registry
     rows (the bus file is the shared state; any node holding the bus
     can reconstruct who exists and when they were last seen). A
     watermark in ``sync_state.json`` makes sync incremental.
  3. Task dispatch + result collection — dispatch posts a real sealed
     task row; workers claim/done it through the bus and report back
     with a ``result`` row; the engine collects those results and
     derives per-task status from bus state, never from memory.
  4. REAL audits —
     * ``health_audit`` computes a 0–100 score from checks it actually
       runs: bus DB present, seal chain verifies, engine files present,
       registry store valid, bus responsive, registry freshness
       (heartbeats inside a staleness window). A tampered bus or a
       stale registry lowers the score by the missing points. Nothing
       is hardcoded: no checks pass, no points.
     * ``sales_audit`` reads real local data files when they exist
       (the estate claims ledger CSV, or a JSON sales/claims file) and
       reports the numbers it actually parsed. When no data file is
       present it says so — ``available: False`` and ``None`` figures —
       instead of inventing a report.

Bus access mirrors console.py exactly: the ApexYX bus library
(``mesh_bus.py``) is loaded from the sibling ApexYX-Sovereign checkout
(``APEX_BUS_PATH`` overrides), and the data directory resolves as
explicit arg > ``$MESH_DIR`` > a local ``.mesh`` folder beside this
file. Python 3 standard library only. The engine moves and audits work;
executing tasks remains a worker's job.
"""

import csv
import importlib.util
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))

REGISTRY_FILE = "registry.json"
SYNC_STATE_FILE = "sync_state.json"
REGISTRY_KIND = "registry"
RESULT_KIND = "result"
TASK_KIND = "task"
ENGINE_NODE = "apex-core"

DEFAULT_STALE_AFTER = 3600  # seconds; a heartbeat older than this is stale


def _default_bus_path():
    # Same lookup as console.py: canonical repo name or the lowercase
    # sibling layout; APEX_BUS_PATH overrides either.
    for _name in ("apexyx-sovereign", "ApexYX-Sovereign"):
        _cand = os.path.join(HERE, "..", _name, "mesh_bus", "mesh_bus.py")
        if os.path.exists(_cand):
            return _cand
    return os.path.join(HERE, "..", "apexyx-sovereign",
                        "mesh_bus", "mesh_bus.py")


DEFAULT_BUS_PATH = _default_bus_path()
DEFAULT_MESH_DIR = os.path.join(HERE, ".mesh")

_bus_module = None


# ---------------------------------------------------------------- bus loading

def mesh_dir(mesh_dir_arg=None):
    """Resolve the bus data directory: explicit arg > $MESH_DIR > ./.mesh."""
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
        spec = importlib.util.spec_from_file_location("mesh_bus_engine",
                                                      bus_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _bus_module = module
    _bus_module.MESH_DIR = resolved
    os.environ["MESH_DIR"] = resolved
    return _bus_module, resolved


def _connect(mesh_dir_arg=None):
    bus, resolved = _load_bus(mesh_dir_arg)
    return bus, bus.db(), resolved


def _now(now=None):
    return int(time.time()) if now is None else int(now)


# ---------------------------------------------------------------- persistence

def _atomic_write_json(path, payload):
    tmp = "%s.tmp-%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, type(default)) else default
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------- 1. registry

def _registry_path(resolved):
    return os.path.join(resolved, REGISTRY_FILE)


def load_registry(mesh_dir_arg=None):
    """Read the persisted registry from disk.

    Returns {"agents": {name: {...}}, "updated": ts}. A missing or
    corrupt store reads as an empty registry — callers that need to
    distinguish "empty" from "broken" use health_audit, which checks
    the store file directly.
    """
    _, resolved = _load_bus(mesh_dir_arg)
    data = _read_json(_registry_path(resolved), {"agents": {}})
    if not isinstance(data.get("agents"), dict):
        data["agents"] = {}
    return data


def _save_registry(registry, resolved):
    registry["updated"] = _now()
    _atomic_write_json(_registry_path(resolved), registry)


def register_agent(name, role="", capabilities=None, node="",
                   mesh_dir_arg=None, now=None):
    """Register an agent and persist it; also announce it on the bus.

    Re-registering an existing name updates role/capabilities and
    counts as a heartbeat. Returns the stored agent record (a dict).
    Raises ValueError on an empty name.
    """
    name = str(name or "").strip()
    if not name:
        raise ValueError("agent name must not be empty")
    ts = _now(now)
    bus, conn, resolved = _connect(mesh_dir_arg)
    try:
        registry = load_registry(mesh_dir_arg)
        agents = registry["agents"]
        rec = agents.get(name, {})
        rec.update({
            "name": name,
            "role": str(role or rec.get("role", "")),
            "capabilities": list(capabilities
                                 if capabilities is not None
                                 else rec.get("capabilities", [])),
            "node": str(node or rec.get("node", "")),
            "registered_ts": int(rec.get("registered_ts") or ts),
            "last_heartbeat": ts,
            "heartbeats": int(rec.get("heartbeats", 0)) + 1,
        })
        agents[name] = rec
        _save_registry(registry, resolved)
        bus.post(conn, node or ENGINE_NODE, REGISTRY_KIND, json.dumps({
            "event": "register", "agent": name, "role": rec["role"],
            "capabilities": rec["capabilities"], "node": rec["node"],
            "ts": ts,
        }), tgt="")
    finally:
        conn.close()
    return dict(rec)


def heartbeat(name, mesh_dir_arg=None, now=None):
    """Record a heartbeat for a registered agent (bus + local store).

    Raises LookupError for an unknown agent — a heartbeat from an
    unregistered name is a bug, not a registration.
    """
    name = str(name or "").strip()
    ts = _now(now)
    bus, conn, resolved = _connect(mesh_dir_arg)
    try:
        registry = load_registry(mesh_dir_arg)
        rec = registry["agents"].get(name)
        if rec is None:
            raise LookupError("no registered agent named %r" % name)
        rec["last_heartbeat"] = ts
        rec["heartbeats"] = int(rec.get("heartbeats", 0)) + 1
        _save_registry(registry, resolved)
        bus.post(conn, rec.get("node") or ENGINE_NODE, REGISTRY_KIND,
                 json.dumps({"event": "heartbeat", "agent": name,
                             "ts": ts}), tgt="")
    finally:
        conn.close()
    return dict(rec)


def list_agents(mesh_dir_arg=None, stale_after=DEFAULT_STALE_AFTER,
                now=None):
    """All registered agents, each annotated with age + fresh/stale.

    Returns a list of dicts sorted by name. `status` is "fresh" when
    the last heartbeat is within `stale_after` seconds of `now`,
    else "stale". The annotation is computed at read time — the stored
    record is never rewritten by a listing.
    """
    ts = _now(now)
    registry = load_registry(mesh_dir_arg)
    out = []
    for name in sorted(registry["agents"]):
        rec = dict(registry["agents"][name])
        age = ts - int(rec.get("last_heartbeat", 0))
        rec["age_seconds"] = age
        rec["status"] = "fresh" if age <= int(stale_after) else "stale"
        out.append(rec)
    return out


# ---------------------------------------------------------------- 2. sync

def _sync_state_path(resolved):
    return os.path.join(resolved, SYNC_STATE_FILE)


def sync_state(mesh_dir_arg=None):
    """Fold the bus's registry rows into the local registry store.

    Reads kind="registry" rows past the stored watermark, applies
    register/heartbeat events in bus order (newest event wins per
    field; a heartbeat never moves last_heartbeat backwards), advances
    the watermark, and persists both files. This is the mechanism that
    lets any node holding the bus file reconstruct the estate's agent
    registry — the local registry.json is a cache, the bus is truth.

    Returns {"applied": n_rows_applied, "agents": [names...],
             "watermark": last_bus_id_consumed}.
    """
    bus, conn, resolved = _connect(mesh_dir_arg)
    try:
        state = _read_json(_sync_state_path(resolved),
                           {"last_registry_id": 0})
        watermark = int(state.get("last_registry_id", 0))
        rows = bus.export(conn, kind=REGISTRY_KIND, since=watermark,
                          limit=100000)
        registry = load_registry(mesh_dir_arg)
        agents = registry["agents"]
        applied = 0
        for row in rows:
            watermark = max(watermark, int(row["id"]))
            try:
                event = json.loads(row["text"])
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            name = str(event.get("agent") or "").strip()
            if not name:
                continue
            ts = int(event.get("ts") or row["ts"] or 0)
            rec = agents.get(name, {"name": name, "role": "",
                                    "capabilities": [], "node": "",
                                    "registered_ts": ts,
                                    "last_heartbeat": 0, "heartbeats": 0})
            if event.get("event") == "register":
                rec["role"] = str(event.get("role", rec.get("role", "")))
                if isinstance(event.get("capabilities"), list):
                    rec["capabilities"] = event["capabilities"]
                rec["node"] = str(event.get("node", rec.get("node", "")))
                rec["registered_ts"] = int(rec.get("registered_ts") or ts)
            if ts >= int(rec.get("last_heartbeat", 0)):
                rec["last_heartbeat"] = ts
            rec["heartbeats"] = int(rec.get("heartbeats", 0)) + 1
            agents[name] = rec
            applied += 1
        _save_registry(registry, resolved)
        _atomic_write_json(_sync_state_path(resolved),
                           {"last_registry_id": watermark,
                            "last_sync_ts": _now()})
    finally:
        conn.close()
    return {"applied": applied, "agents": sorted(agents),
            "watermark": watermark}


def export_state(mesh_dir_arg=None):
    """A snapshot of everything the engine knows, for cross-node diffing:
    the registry, the sync watermark, and the bus's real counts."""
    bus, conn, resolved = _connect(mesh_dir_arg)
    try:
        status = bus.status(conn)
    finally:
        conn.close()
    state = _read_json(_sync_state_path(resolved), {"last_registry_id": 0})
    return {
        "mesh_dir": resolved,
        "registry": load_registry(mesh_dir_arg),
        "sync": {"last_registry_id": int(state.get("last_registry_id", 0)),
                 "last_sync_ts": state.get("last_sync_ts")},
        "bus": {"total": status.get("total", 0),
                "by_state": status.get("by_state", {}),
                "by_kind": status.get("by_kind", {})},
    }


# ------------------------------------------------------- 3. dispatch + results

def dispatch(text, target="", node=ENGINE_NODE, mesh_dir_arg=None):
    """Post a real task to the bus. Returns the bus row id (int).

    Raises ValueError on empty text, exactly like the console.
    """
    if text is None or not str(text).strip():
        raise ValueError("task text must not be empty")
    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        return int(bus.post(conn, node, TASK_KIND, str(text).strip(),
                            target or ""))
    finally:
        conn.close()


def submit_result(task_id, ok, detail="", node=ENGINE_NODE,
                  mesh_dir_arg=None):
    """The worker side of dispatch: post a result row for a task.

    The payload is JSON on a kind="result" bus row targeted at the
    dispatching node, so results ride the same sealed chain as tasks.
    Returns the result row's bus id. Raises LookupError if the task
    does not exist.
    """
    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        row = conn.execute("SELECT id FROM messages WHERE id=?",
                           (int(task_id),)).fetchone()
        if row is None:
            raise LookupError("no bus task with id %s" % task_id)
        payload = json.dumps({"task_id": int(task_id), "ok": bool(ok),
                              "detail": str(detail), "by": node,
                              "ts": _now()})
        return int(bus.post(conn, node, RESULT_KIND, payload,
                            tgt=ENGINE_NODE))
    finally:
        conn.close()


def collect_results(since=0, mesh_dir_arg=None):
    """Read result rows off the bus, newest last.

    Each entry: {"result_id", "task_id", "ok", "detail", "by", "ts"}.
    Rows whose payload is not a well-formed result are skipped — the
    bus tolerates foreign rows, the engine ignores what it can't parse.
    """
    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        rows = bus.export(conn, kind=RESULT_KIND, since=int(since),
                          limit=100000)
    finally:
        conn.close()
    out = []
    for row in rows:
        try:
            payload = json.loads(row["text"])
            task_id = int(payload["task_id"])
        except (ValueError, KeyError, TypeError):
            continue
        out.append({
            "result_id": int(row["id"]),
            "task_id": task_id,
            "ok": bool(payload.get("ok")),
            "detail": str(payload.get("detail", "")),
            "by": str(payload.get("by", row["node"])),
            "ts": int(payload.get("ts") or row["ts"]),
        })
    return out


def task_status(task_id, mesh_dir_arg=None):
    """One task's real status, derived from the bus at read time:
    {"id", "state", "claimed_by", "result": {...} | None}.

    Raises LookupError for a missing id.
    """
    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        row = conn.execute("SELECT * FROM messages WHERE id=?",
                           (int(task_id),)).fetchone()
        if row is None:
            raise LookupError("no bus task with id %s" % task_id)
        state, claimed_by = row["state"], row["claimed_by"]
    finally:
        conn.close()
    result = None
    for entry in collect_results(mesh_dir_arg=mesh_dir_arg):
        if entry["task_id"] == int(task_id):
            result = entry  # newest wins: rows arrive in id order
    return {"id": int(task_id), "state": state, "claimed_by": claimed_by,
            "result": result}


# ---------------------------------------------------------------- 4a. health audit

def health_audit(mesh_dir_arg=None, stale_after=DEFAULT_STALE_AFTER,
                 now=None):
    """Compute the engine's health score from checks actually run.

    Six checks, 100 points total. Every point is earned by a check
    executing against the real bus/files right now; a failed check
    contributes 0 (or, for freshness, its earned fraction) and says
    why. Returns {"score", "max_score": 100, "checks": [...],
    "mesh_dir", "audited_ts"}.
    """
    ts = _now(now)
    _, resolved = _load_bus(mesh_dir_arg)
    checks = []

    def add(name, earned, possible, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "points": earned,
                       "max_points": possible, "detail": detail})

    # -- bus DB present (checked BEFORE connecting: db() creates it) --
    db_file = os.path.join(resolved, "bus.db")
    present = os.path.isfile(db_file) and os.path.getsize(db_file) > 0
    add("bus_db_present", 10 if present else 0, 10, present,
        "bus.db %s at %s" % ("present (%d bytes)" % os.path.getsize(db_file)
                             if present else "missing or empty", db_file))

    bus, conn, _ = _connect(mesh_dir_arg)
    try:
        # -- seal chain verifies --
        bad = [int(i) for i in bus.verify(conn)]
        add("bus_seal_chain", 30 if not bad else 0, 30, not bad,
            "seal chain intact" if not bad
            else "seal mismatch on row(s) %s" % bad)

        # -- bus responsive: status answers and agrees with a raw count --
        try:
            st = bus.status(conn)
            raw_total = conn.execute(
                "SELECT COUNT(*) FROM messages").fetchone()[0]
            responsive = int(st.get("total", -1)) == int(raw_total)
            detail = "bus.status total=%s, raw count=%s" % (
                st.get("total"), raw_total)
        except Exception as exc:  # noqa: BLE001 - audit reports, not hides
            responsive, detail = False, "bus.status raised %r" % (exc,)
        add("bus_responsive", 10 if responsive else 0, 10, responsive,
            detail)
    finally:
        conn.close()

    # -- engine files present --
    wanted = ["console.py", "scionix_core.py"]
    missing = [f for f in wanted
               if not os.path.isfile(os.path.join(HERE, f))]
    add("engine_files_present", 15 if not missing else 0, 15,
        not missing,
        "console.py + scionix_core.py present beside the engine"
        if not missing else "missing file(s): %s" % ", ".join(missing))

    # -- registry store valid --
    reg_file = _registry_path(resolved)
    store_ok, store_detail = False, "registry.json not written yet"
    if os.path.isfile(reg_file):
        try:
            with open(reg_file, "r", encoding="utf-8") as fh:
                parsed = json.load(fh)
            store_ok = isinstance(parsed, dict) \
                and isinstance(parsed.get("agents"), dict)
            store_detail = ("registry.json valid, %d agent(s) stored"
                            % len(parsed.get("agents", {}))) if store_ok \
                else "registry.json parses but has no agents object"
        except ValueError as exc:
            store_detail = "registry.json is not valid JSON: %s" % exc
    add("registry_store_valid", 10 if store_ok else 0, 10, store_ok,
        store_detail)

    # -- registry freshness: fraction of agents heartbeat-fresh --
    agents = list_agents(mesh_dir_arg=mesh_dir_arg,
                         stale_after=stale_after, now=ts)
    if agents:
        fresh = sum(1 for a in agents if a["status"] == "fresh")
        earned = int(round(25.0 * fresh / len(agents)))
        add("registry_freshness", earned, 25, fresh == len(agents),
            "%d/%d agent(s) heartbeat-fresh within %ds"
            % (fresh, len(agents), int(stale_after)))
    else:
        add("registry_freshness", 0, 25, False,
            "no agents registered — freshness cannot be earned")

    score = sum(c["points"] for c in checks)
    return {"score": score, "max_score": 100, "checks": checks,
            "mesh_dir": resolved, "audited_ts": ts}


# ---------------------------------------------------------------- 4b. sales audit

def _default_sales_paths():
    """Candidate local data files for the sales/claims audit, in order:
    an explicit env override, the estate claims ledger, then files
    beside the engine. Only files that exist are read."""
    paths = []
    env_path = os.environ.get("APEX_SALES_FILE")
    if env_path:
        paths.append(env_path)
    paths.append(os.path.expanduser(
        "~/workspace/capability-stack/claims.csv"))
    paths.append(os.path.join(HERE, "claims.csv"))
    paths.append(os.path.join(HERE, "sales.json"))
    return paths


_NUMERIC_CLAIM_COLUMNS = ("verified_claims_total", "claims",
                          "verified_claims", "sales", "orders", "count",
                          "total")


def _audit_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return {"available": True, "source": path, "rows": 0,
                "claims_total": None,
                "detail": "file exists but contains no data rows"}
    headers = [h for h in rows[0].keys() if h]
    column = next((c for c in _NUMERIC_CLAIM_COLUMNS
                   if c in {h.strip().lower(): h for h in headers}),
                  None)
    if column is None:
        return {"available": True, "source": path, "rows": len(rows),
                "claims_total": None,
                "detail": "no recognised numeric claims/sales column in "
                          "headers %s" % headers}
    key = {h.strip().lower(): h for h in headers}[column]
    total, parsed = 0, 0
    for row in rows:
        try:
            total += int(float(str(row.get(key, "")).strip()))
            parsed += 1
        except (TypeError, ValueError):
            continue
    latest = rows[-1]
    return {"available": True, "source": path, "rows": len(rows),
            "claims_total": total if parsed else None,
            "latest_row": {k: latest.get(k) for k in headers},
            "detail": "summed column %r over %d parseable row(s)"
                      % (key, parsed)}


def _audit_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {"available": True, "source": path, "claims_total": None,
                "detail": "JSON root is not an object — nothing to sum"}
    figures = {}
    for key, value in data.items():
        low = str(key).lower()
        if isinstance(value, (int, float)) and any(
                word in low for word in ("claim", "sale", "order",
                                         "revenue")):
            figures[str(key)] = value
    return {"available": True, "source": path, "figures": figures,
            "claims_total": figures.get("claims",
                                        figures.get("verified_claims")),
            "detail": "numeric sales/claims figures read from JSON keys: %s"
                      % (sorted(figures) if figures else "none found")}


def sales_audit(paths=None):
    """Audit sales/claims from real local data files — or say "no data".

    Tries each candidate path in order and audits the first file that
    exists. When none exists, returns available=False with every
    figure None and the paths tried. This function never invents a
    number: every figure in an available=True result was parsed from
    the named file during this call.
    """
    candidates = list(paths) if paths is not None \
        else _default_sales_paths()
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                if str(path).lower().endswith(".json"):
                    return _audit_json(path)
                return _audit_csv(path)
            except (OSError, ValueError, csv.Error) as exc:
                return {"available": True, "source": path,
                        "claims_total": None,
                        "detail": "file present but unreadable: %r" % (exc,)}
    return {"available": False, "source": None, "claims_total": None,
            "paths_tried": candidates,
            "detail": "no data: no claims/sales data file found at any "
                      "candidate path"}


def full_audit(mesh_dir_arg=None, stale_after=DEFAULT_STALE_AFTER,
               now=None, sales_paths=None):
    """Both audits, one call: computed health + honest sales."""
    return {
        "health": health_audit(mesh_dir_arg=mesh_dir_arg,
                               stale_after=stale_after, now=now),
        "sales": sales_audit(paths=sales_paths),
    }

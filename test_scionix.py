#!/usr/bin/env python3
"""Verification for scionix_core.py — the Apex Core engine.

Runs the engine against a THROWAWAY MESH_DIR and fixture files only:

  1. registry round-trip: register + heartbeat persist to disk and
     re-read with correct freshness annotation
  2. sync: wipe the local registry store, rebuild it from bus rows
  3. dispatch -> result: a task dispatched by the engine is claimed,
     completed and answered on the bus; collect_results finds it and
     task_status agrees with the bus
  4. health audit is COMPUTED: a healthy fixture scores high; a
     tampered bus (direct sqlite edit) fails the seal check and the
     score drops by the seal check's points
  5. sales audit honesty: no data file -> available=False, figures
     None; a real fixture CSV -> the exact summed total

Prints PASS/FAIL lines + a summary; exits non-zero on any FAIL.
Python 3 standard library only.
"""

import csv
import os
import shutil
import sqlite3
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix="apex-core-engine-test.")
os.environ["MESH_DIR"] = TMP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scionix_core as engine  # noqa: E402

RESULTS = []
T0 = 1_800_000_000  # fixed clock base so freshness math is deterministic


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name,
                        (" — %s" % detail) if detail else ""))


def main():
    # 1 — registry round-trip -------------------------------------------
    try:
        engine.register_agent("alpha", role="builder",
                              capabilities=["code"], node="pixel",
                              mesh_dir_arg=TMP, now=T0)
        engine.register_agent("beta", role="scout", mesh_dir_arg=TMP,
                              now=T0)
        engine.heartbeat("alpha", mesh_dir_arg=TMP, now=T0 + 10)
        on_disk = os.path.isfile(os.path.join(TMP, "registry.json"))
        agents = {a["name"]: a
                  for a in engine.list_agents(mesh_dir_arg=TMP, now=T0 + 20)}
        alpha, beta = agents.get("alpha", {}), agents.get("beta", {})
        check("1 registry round-trip persists and re-reads",
              on_disk and len(agents) == 2
              and alpha.get("role") == "builder"
              and alpha.get("capabilities") == ["code"]
              and alpha.get("heartbeats") == 2
              and alpha.get("status") == "fresh"
              and beta.get("status") == "fresh",
              "agents=%r" % (agents,))
        stale = {a["name"]: a for a in engine.list_agents(
            mesh_dir_arg=TMP, stale_after=60, now=T0 + 7200)}
        check("1b freshness annotation ages honestly",
              stale.get("alpha", {}).get("status") == "stale"
              and stale.get("beta", {}).get("status") == "stale",
              "statuses=%r" % ({k: v.get("status")
                                for k, v in stale.items()},))
        try:
            engine.heartbeat("ghost", mesh_dir_arg=TMP)
            ghost_ok = False
        except LookupError:
            ghost_ok = True
        check("1c heartbeat for an unknown agent raises LookupError",
              ghost_ok)
    except Exception as exc:  # noqa: BLE001
        check("1 registry round-trip persists and re-reads", False,
              "raised %r" % (exc,))

    # 2 — sync rebuilds the local store from bus rows --------------------
    try:
        os.remove(os.path.join(TMP, "registry.json"))
        state_file = os.path.join(TMP, "sync_state.json")
        if os.path.exists(state_file):
            os.remove(state_file)
        summary = engine.sync_state(mesh_dir_arg=TMP)
        rebuilt = {a["name"]
                   for a in engine.list_agents(mesh_dir_arg=TMP, now=T0)}
        check("2 sync rebuilds the registry from bus rows",
              summary.get("applied") >= 3
              and rebuilt == {"alpha", "beta"}
              and summary.get("watermark", 0) > 0,
              "summary=%r rebuilt=%r" % (summary, rebuilt))
        again = engine.sync_state(mesh_dir_arg=TMP)
        check("2b second sync is incremental (nothing new to apply)",
              again.get("applied") == 0
              and again.get("watermark") == summary.get("watermark"),
              "again=%r" % (again,))
    except Exception as exc:  # noqa: BLE001
        check("2 sync rebuilds the registry from bus rows", False,
              "raised %r" % (exc,))

    # 3 — dispatch -> result on the temp bus -----------------------------
    try:
        tid = engine.dispatch("engine smoke task", target="beta",
                              mesh_dir_arg=TMP)
        # the worker side, driven through the bus the console fronts:
        import importlib.util
        bus_path = os.path.abspath(os.environ.get(
            "APEX_BUS_PATH", engine.DEFAULT_BUS_PATH))
        spec = importlib.util.spec_from_file_location("mesh_bus_t",
                                                      bus_path)
        bus = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bus)
        bus.MESH_DIR = TMP
        conn = bus.db()
        won = bus.claim(conn, tid, "beta")
        closed = bus.done(conn, tid, "beta")
        conn.close()
        engine.submit_result(tid, True, "smoke done", node="beta",
                             mesh_dir_arg=TMP)
        results = [r for r in engine.collect_results(mesh_dir_arg=TMP)
                   if r["task_id"] == tid]
        status = engine.task_status(tid, mesh_dir_arg=TMP)
        check("3 dispatch -> claim/done -> collected result",
              isinstance(tid, int) and won and closed
              and len(results) == 1 and results[0]["ok"] is True
              and results[0]["detail"] == "smoke done"
              and status.get("state") == "done"
              and status.get("result", {}).get("ok") is True,
              "tid=%r results=%r status=%r" % (tid, results, status))
        try:
            engine.dispatch("   ", mesh_dir_arg=TMP)
            empty_ok = False
        except ValueError:
            empty_ok = True
        check("3b empty dispatch raises ValueError", empty_ok)
    except Exception as exc:  # noqa: BLE001
        check("3 dispatch -> claim/done -> collected result", False,
              "raised %r" % (exc,))

    # 4 — health audit is computed, and damage lowers it -----------------
    try:
        healthy = engine.health_audit(mesh_dir_arg=TMP, now=T0 + 30)
        by_name = {c["name"]: c for c in healthy["checks"]}
        check("4 health audit: healthy fixture earns a high score",
              healthy["score"] >= 90
              and by_name["bus_seal_chain"]["ok"] is True
              and by_name["registry_freshness"]["points"] == 25,
              "score=%r checks=%r" % (
                  healthy["score"],
                  {k: v["points"] for k, v in by_name.items()}))
        db_file = os.path.join(TMP, "bus.db")
        raw = sqlite3.connect(db_file)
        raw.execute("UPDATE messages SET text='TAMPERED BY TEST' "
                    "WHERE id=(SELECT MIN(id) FROM messages)")
        raw.commit()
        raw.close()
        damaged = engine.health_audit(mesh_dir_arg=TMP, now=T0 + 30)
        d_by_name = {c["name"]: c for c in damaged["checks"]}
        check("4b tampered bus fails the seal check and lowers the score",
              d_by_name["bus_seal_chain"]["ok"] is False
              and damaged["score"] == healthy["score"] - 30,
              "healthy=%r damaged=%r" % (healthy["score"],
                                         damaged["score"]))
        stale = engine.health_audit(mesh_dir_arg=TMP, now=T0 + 100000)
        s_by_name = {c["name"]: c for c in stale["checks"]}
        check("4c stale heartbeats earn no freshness points",
              s_by_name["registry_freshness"]["points"] == 0
              and stale["score"] < damaged["score"],
              "stale_score=%r" % (stale["score"],))
    except Exception as exc:  # noqa: BLE001
        check("4 health audit: healthy fixture earns a high score", False,
              "raised %r" % (exc,))

    # 5 — sales audit: honest no-data, exact figures when data exists ----
    try:
        missing = os.path.join(TMP, "definitely-absent.csv")
        nodata = engine.sales_audit(paths=[missing])
        check("5 sales audit reports no data honestly",
              nodata.get("available") is False
              and nodata.get("claims_total") is None
              and "no data" in nodata.get("detail", ""),
              "nodata=%r" % (nodata,))
        fixture = os.path.join(TMP, "claims-fixture.csv")
        with open(fixture, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["date", "verified_claims_total", "source"])
            writer.writerow(["2026-10-27", 3, "fixture"])
            writer.writerow(["2026-10-28", 4, "fixture"])
        real = engine.sales_audit(paths=[fixture])
        check("5b sales audit sums a real fixture exactly",
              real.get("available") is True
              and real.get("claims_total") == 7
              and real.get("rows") == 2
              and real.get("latest_row", {}).get("date") == "2026-10-28",
              "real=%r" % (real,))
    except Exception as exc:  # noqa: BLE001
        check("5 sales audit reports no data honestly", False,
              "raised %r" % (exc,))

    passed = sum(1 for _, ok in RESULTS if ok)
    print("\n%d/%d checks passed (throwaway MESH_DIR: %s)"
          % (passed, len(RESULTS), TMP))
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())

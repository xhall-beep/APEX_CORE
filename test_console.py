#!/usr/bin/env python3
"""Verification for the APEX Core console (Q3).

Runs the console's control layer against a THROWAWAY MESH_DIR and checks
real bus effects — nothing is mocked:

  1. dispatch through the console appears on the bus with the returned id
  2. claim+complete through the console moves the counts (done=1)
  3. verify_chain reports INTACT on the untouched chain
  4. a direct sqlite tamper makes verify_chain report TAMPERED
  5. dispatch with empty text is rejected with a real error

Prints PASS/FAIL lines + a summary; exits non-zero on any FAIL.
Python 3 standard library only.
"""

import os
import shutil
import sqlite3
import sys
import tempfile

# Point the bus at a throwaway directory BEFORE importing the console,
# so no run can ever touch a real bus (never ~/.mesh, never ./.mesh).
TMP = tempfile.mkdtemp(prefix="apex-core-test.")
os.environ["MESH_DIR"] = TMP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name,
                        (" — %s" % detail) if detail else ""))


def main():
    text = "Q3 smoke task: prove the console moves real bus rows"

    # 1 — dispatch through the console layer, then find it on the bus.
    tid = None
    try:
        tid = console.dispatch_task(text, mesh_dir_arg=TMP)
        rows = console.list_tasks(n=20, mesh_dir_arg=TMP)
        mine = [r for r in rows if r["id"] == tid]
        check("1 dispatch returns a real bus id found in list_tasks",
              isinstance(tid, int) and len(mine) == 1
              and mine[0]["text"] == text and mine[0]["state"] == "new",
              "id=%r rows=%d" % (tid, len(rows)))
    except Exception as exc:  # noqa: BLE001 - report, then fail the check
        check("1 dispatch returns a real bus id found in list_tasks",
              False, "raised %r" % (exc,))

    # 2 — claim+complete through the console; status counts must move.
    try:
        before = console.bus_health(mesh_dir_arg=TMP)
        result = console.complete_task(tid, mesh_dir_arg=TMP)
        after = console.bus_health(mesh_dir_arg=TMP)
        check("2 complete_task moves bus counts to done=1",
              result.get("done") is True and result.get("state") == "done"
              and after.get("done") == 1
              and after.get("new") == before.get("new") - 1,
              "result=%r before_new=%r after=%r"
              % (result, before.get("new"),
                 {k: after.get(k) for k in ("new", "claimed", "done")}))
    except Exception as exc:  # noqa: BLE001
        check("2 complete_task moves bus counts to done=1",
              False, "raised %r" % (exc,))

    # 3 — seal chain intact after honest console use.
    try:
        verdict = console.verify_chain(mesh_dir_arg=TMP)
        check("3 verify_chain reports INTACT on the untouched chain",
              verdict.get("ok") is True
              and verdict.get("verdict") == "INTACT"
              and verdict.get("bad_rows") == [],
              "verdict=%r" % (verdict,))
    except Exception as exc:  # noqa: BLE001
        check("3 verify_chain reports INTACT on the untouched chain",
              False, "raised %r" % (exc,))

    # 4 — tamper with the bus DB directly; verify must name the row.
    try:
        db_file = os.path.join(TMP, "bus.db")
        raw = sqlite3.connect(db_file)
        raw.execute("UPDATE messages SET text='TAMPERED BY TEST' WHERE id=?",
                    (tid,))
        raw.commit()
        raw.close()
        verdict = console.verify_chain(mesh_dir_arg=TMP)
        check("4 verify_chain reports TAMPERED after a direct sqlite edit",
              verdict.get("ok") is False
              and verdict.get("verdict") == "TAMPERED"
              and tid in verdict.get("bad_rows", []),
              "verdict=%r" % (verdict,))
    except Exception as exc:  # noqa: BLE001
        check("4 verify_chain reports TAMPERED after a direct sqlite edit",
              False, "raised %r" % (exc,))

    # 5 — empty dispatch is rejected with a real error, and posts nothing.
    try:
        total_before = console.bus_health(mesh_dir_arg=TMP).get("total")
        rejected = False
        for bad_text in ("", "   ", None):
            try:
                console.dispatch_task(bad_text, mesh_dir_arg=TMP)
            except ValueError:
                rejected = True
            else:
                rejected = False
        total_after = console.bus_health(mesh_dir_arg=TMP).get("total")
        check("5 empty dispatch is rejected and posts nothing",
              rejected and total_after == total_before,
              "total before=%r after=%r" % (total_before, total_after))
    except Exception as exc:  # noqa: BLE001
        check("5 empty dispatch is rejected and posts nothing",
              False, "raised %r" % (exc,))

    passed = sum(1 for _, ok in RESULTS if ok)
    print("\n%d/%d checks passed (throwaway MESH_DIR: %s)"
          % (passed, len(RESULTS), TMP))
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())

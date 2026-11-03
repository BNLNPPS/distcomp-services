#!/usr/bin/env python3
"""End Harvester workers whose batch job the local HTCondor schedd no longer holds.

The installed worker-safety change keeps an HTCondor worker of unknown state
past checkTimeout (CHANGES.md, 2026-10-25). A worker whose job left the schedd
without a terminal record therefore keeps its status and counts against the
queue's worker limits indefinitely; the sweeper's kill finds nothing to remove
and changes nothing. This tool ends such workers as cancelled.

A worker is ended only when all of the following hold:
  - it is at --site, in one of --status, and was submitted before --before;
  - the schedd query succeeds and holds no job with the worker's batchID;
  - it carries no PanDA job (no row in jw_table).

Each change goes through Harvester's WorkSpec.set_status and
DBProxy.update_worker with the old status as the condition, so the end time is
set and the change reaches PanDA by the propagator's normal path. A failed
schedd or history query stops the run before anything changes. --dry-run lists
and changes nothing. Each run appends one JSON line to --log.

Run on osgsub01 as atlpan with Harvester's interpreter and environment:

  sudo runuser -u atlpan -- bash -c 'set -a; . /opt/harvester/etc/sysconfig/panda_harvester_env; set +a;
    /opt/harvester/bin/python reconcile-vanished-workers.py --site BNL_OSG_PanDA_1 --before 2026-11-01T00:00 --dry-run'
"""

import argparse
import collections
import datetime
import json
import os
import socket
import sys

import htcondor
from pandaharvester.harvestercore.db_proxy import DBProxy
from pandaharvester.harvestercore.work_spec import WorkSpec

DEFAULT_LOG = "/var/data/atlpan/harvester_common/worker-reconcile/reconcile.log"
JOB_STATUS = {1: "idle", 2: "running", 3: "removed", 4: "completed", 5: "held", 6: "transferring", 7: "suspended"}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="computingSite (PanDA queue)")
    parser.add_argument("--status", nargs="+", default=[WorkSpec.ST_submitted], help="worker statuses to consider")
    parser.add_argument("--before", required=True, help="only workers submitted before this UTC time, YYYY-MM-DDTHH:MM")
    parser.add_argument("--reason", default="batch job absent from the schedd; reconciled by hand", help="diagnostic recorded on each worker")
    parser.add_argument("--log", default=DEFAULT_LOG)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    before = datetime.datetime.fromisoformat(args.before)

    proxy = DBProxy()
    marks = ",".join(f":st{i}" for i in range(len(args.status)))
    var_map = {f":st{i}": s for i, s in enumerate(args.status)}
    var_map.update({":site": args.site, ":before": before})
    proxy.execute(
        f"SELECT workerID, batchID, status, submitTime FROM work_table "
        f"WHERE computingSite=:site AND status IN ({marks}) AND submitTime<:before",
        var_map,
    )
    candidates = proxy.cur.fetchall()

    proxy.execute(
        f"SELECT DISTINCT w.workerID FROM work_table w JOIN jw_table j ON j.workerID=w.workerID "
        f"WHERE w.computingSite=:site AND w.status IN ({marks}) AND w.submitTime<:before",
        var_map,
    )
    with_jobs = {row[0] for row in proxy.cur.fetchall()}

    # Every job the schedd holds; a failed query raises and stops the run.
    schedd = htcondor.Schedd()
    in_queue = {f"{ad['ClusterId']}.{ad['ProcId']}" for ad in schedd.query(constraint="true", projection=["ClusterId", "ProcId"])}

    batch_ids = [b for _, b, _, _ in candidates if b]
    history = {}
    if batch_ids:
        clusters = sorted({int(b.split(".")[0]) for b in batch_ids})
        constraint = f"ClusterId >= {clusters[0]} && ClusterId <= {clusters[-1]}"
        for ad in schedd.history(constraint, ["ClusterId", "ProcId", "JobStatus"]):
            history[f"{ad['ClusterId']}.{ad['ProcId']}"] = JOB_STATUS.get(ad.get("JobStatus"), str(ad.get("JobStatus")))

    to_end, kept = [], collections.Counter()
    for worker_id, batch_id, status, _ in candidates:
        if not batch_id:
            kept["no batchID"] += 1
        elif batch_id in in_queue:
            kept["in the schedd queue"] += 1
        elif worker_id in with_jobs:
            kept["carries a PanDA job"] += 1
        else:
            to_end.append(worker_id)
    history_states = collections.Counter(history.get(b, "no record") for w, b, _, _ in candidates if w in set(to_end))

    ended, failed = 0, []
    if not args.dry_run:
        for worker_id in to_end:
            workspec = proxy.get_worker_with_id(worker_id)
            if workspec is None:
                failed.append(worker_id)
                continue
            old_status = workspec.status
            workspec.set_status(WorkSpec.ST_cancelled)
            workspec.set_dialog_message(args.reason)
            if proxy.update_worker(workspec, {"status": old_status}) == 1:
                ended += 1
            else:
                failed.append(worker_id)

    record = {
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "host": socket.getfqdn(),
        "site": args.site,
        "status": args.status,
        "before": args.before,
        "dry_run": args.dry_run,
        "candidates": len(candidates),
        "submitted_from": str(min((c[3] for c in candidates), default=None)),
        "submitted_to": str(max((c[3] for c in candidates), default=None)),
        "schedd_jobs": len(in_queue),
        "kept": dict(kept),
        "to_end": len(to_end),
        "history_of_to_end": dict(history_states),
        "ended": ended,
        "failed": failed,
    }
    print(json.dumps(record, indent=1))
    if not args.dry_run:
        os.makedirs(os.path.dirname(args.log), exist_ok=True)
        with open(args.log, "a") as handle:
            handle.write(json.dumps(record) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

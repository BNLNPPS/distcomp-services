# osgsub01 changes

Newest first. Every change to Harvester's code goes upstream to HSF/harvester as a pull request (Torre Wenaus, 2026-10-29).

## Local changes on the host

Installed Harvester 0.7.5 from HSF/harvester commit `f44053ba`, under `/opt/harvester/lib/python3.11/site-packages/pandaharvester/`. The comparison of the installed package with that commit ([audit/installed_blobs.py](audit/installed_blobs.py) with [../panda-server/audit/compare.py](../panda-server/audit/compare.py)) must name exactly the files of this table; other differing files are dated backups and an editor copy.

```
ssh ... "ssh osgsub01 'sudo -n /opt/harvester/bin/python -I -'" < audit/installed_blobs.py > /tmp/installed.json
python3 ../panda-server/audit/compare.py /tmp/installed.json <harvester checkout>
```

| File | Change | Since | Upstream |
|---|---|---|---|
| `harvestermonitor/htcondor_monitor.py` | worker safety: a failed schedd query leaves the batch's worker states unchanged and reports the failure, instead of an empty answer that reads every worker as missing; HTCondor workers of unknown state are kept past `checkTimeout`. Regulation: the condor-history age limit has a floor, `monitor.historyMaxAgeFloor` | 2026-10-25; 2026-10-22 | worker safety: **outstanding**, see below. Regulation: **outstanding**, see below |
| `harvesterbody/monitor.py` | worker safety: workers of a failed query keep their status, unchecked, with a `WORKER_STATE_UNVERIFIED` message; a worker of unknown state past `checkTimeout` is kept when the plugin sets `preserveUnknownWorkers`, unless its kill is due, when it is ended as cancelled. Regulation: the FIFO check interval has a ceiling, `monitor.fifoMaxCheckInterval` | 2026-10-25, 2026-11-04; 2026-10-22 | worker safety: **outstanding**, see below. Regulation: **outstanding**, see below |
| `harvestermisc/htcondor_utils.py` | worker safety: a failed command-line query raises | 2026-10-25 | **outstanding**, see below |
| `harvesterbody/cacher.py` | regulation: a per-key refresh interval, `cacher.refreshSecondsByKey` (job statistics refreshed faster than the rest) | 2026-10-22 | **outstanding**, see below |
| `harvesterbody/worker_adjuster.py` | regulation: missing or stale job demand, older than `submitter.jobStatsMaxAge`, holds new pilot submissions (`REGULATION_HOLD`) | 2026-10-22 | **outstanding**, see below |
| `harvesterbody/propagator.py` | a PanDA kill command marks the job's workers to be killed after 600 seconds, so that HTCondor returns the pilot's stdout first; by PanDA operations at BNL, not recorded beyond the comment in the file | 2026-07-09 | not proposed; uses the existing `delay_seconds` of `mark_workers_to_kill_by_pandaid` |

The worker-safety change is on branch `htcondor-query-failure-keeps-workers` of `wenaus/harvester`, off HSF/harvester master, tested 2026-10-30 (the 13 regression checks of swf-epicprod `tests/test_worker_monitor_safety.py` against master's sources; black, isort and flynt; the repository's compile check); pull request HSF/harvester#321, opened 2026-10-30; the ending of a killed worker was added to it on 2026-11-04. In that form, keeping workers of unknown state past `checkTimeout` is the HTCondor monitor option `preserveUnknownWorkers`, off by default, where the installed patch has it always on: a Harvester upgrade that carries the change needs the option set in the monitor section of the `BNL_OSG_PanDA_1` queue configuration.

The regulation changes of 2026-10-22 are installed by swf-epicprod `scripts/configure-osg-regulation.py` and described in swf-epicprod `docs/REGULATION_AUDIT_2026-10-22.md`; each reads a configuration value and does nothing when it is absent. They are on branch `regulation-options` of `wenaus/harvester`, off HSF/harvester master, tested 2026-10-30 (black, isort and flynt; the repository's compile check; each option's own statements run with stubbed boundaries, on the branch and on the four files installed here, with the same results); pull request HSF/harvester#322, opened 2026-10-30. In that form a held submission logs `job statistics missing or older than jobStatsMaxAge=...` instead of `REGULATION_HOLD`, which nothing reads.

## 2026-11-04: the monitor ends a killed worker the schedd no longer holds

- **By:** ePIC production operations (swf-1), on Torre Wenaus's word (dialog, 2026-11-04, "do 2").
- **Why:** the 421 workers ended by hand on 2026-11-03 were killed by Harvester itself: worker 2570166, submitted 2026-10-31 17:23:39 UTC, was marked to kill at 2026-11-02 17:23:54 for queuing longer than `workerQueueTimeLimit` (172800 s), and the sweeper removed its batch job at 17:24:12. From the next check the job was in neither `condor_q` nor the history query, which skips a worker submitted longer ago than the history age limit, so its state was unknown, and the worker-safety change kept it past `checkTimeout` while the sweeper repeated the kill every three minutes (`panda-monitor.log-20261103.gz`, `panda-sweeper.log-20261103.gz`).
- **What:** [patches/killed-unknown-workers/edits.json](patches/killed-unknown-workers/edits.json), built from the installed `harvesterbody/monitor.py` with [../panda-server/patches/prepare.py](../panda-server/patches/prepare.py) and installed with [../panda-server/patches/host-install.py](../panda-server/patches/host-install.py) `--prefix /opt/harvester`: a worker of unknown state past `checkTimeout` whose kill is due (`killTime` set and not in the future) is ended as cancelled, keeping a pilot error already recorded; any other worker of unknown state is kept as before. The same change is on HSF/harvester#321.
- **Installed:** 21:53 UTC (stamp `20261104T2215Z`), `panda_harvester-uwsgi` restarted; record `/opt/harvester/killed-unknown-workers-20261104T2215Z/install.json`. Before: SHA-256 `c257fcea…`, the 2026-10-25 `after` value; after: `606f020c…`.
- **Verified:** the installer's dry run, then the after-checksum read back; the monitor, submitter and sweeper cycling with no error after the restart. Before installation, the branch was run with mocked boundaries: a worker without a kill order, or with a delayed kill not yet due, is kept; a worker whose kill is due is cancelled; without `preserveUnknownWorkers` the timeout kill is unchanged. In the field it acts on the next worker Harvester kills after its batch job has left the history window.
- **Rollback:** `host-install.py --bundle <bundle> --stamp 20261104T2215Z --prefix /opt/harvester --rollback` with the bundle in `/tmp/upgrade-20261104-killed/` (or restore `monitor.py.before-killed-unknown-workers-20261104T2215Z` beside the file, keeping owner and mode), then restart `panda_harvester-uwsgi`.

## 2026-11-03: 421 vanished BNL_OSG_PanDA_1 workers ended as cancelled

- **By:** ePIC production operations (swf-1), on Torre Wenaus's word (dialog, 2026-11-03 10:12 ET).
- **Why:** Harvester held 421 `BNL_OSG_PanDA_1` workers as `submitted`, submitted 2026-10-31 17:23-17:56 UTC. The schedd held none of them and its history recorded all 421 as removed. The worker-safety change keeps an HTCondor worker of unknown state past `checkTimeout`, and the sweeper's kill, repeated every cycle since, found nothing to remove and changed nothing, so the 421 counted against the queue's waiting limit of 600: Harvester submitted no pilot for activated jobs (four canary jobs waited from 2026-11-03 03:07 ET) and could have added at most 179.
- **What:** [reconcile-vanished-workers.py](reconcile-vanished-workers.py), installed in `/var/data/atlpan/harvester_common/worker-reconcile/`, run as `atlpan` with `--site BNL_OSG_PanDA_1 --before 2026-11-01T00:00` at 15:16 UTC: 421 candidates, schedd queue empty, none carrying a PanDA job, history `removed` for all 421; 421 set to `cancelled` with Harvester's `WorkSpec.set_status` and `DBProxy.update_worker` (condition: status still `submitted`), diagnostic "batch job removed (condor history) and absent from the schedd". Record line in `reconcile.log` there.
- **Verified:** the dry run listed exactly the 421 before the change; the run reported 421 ended, none failed. By 15:20 UTC PanDA's `harvester_workers` held the 421 as cancelled, Harvester had submitted 8 new pilots for the queue and 4 were running.
- **Rollback:** none applicable; the batch jobs no longer exist.
- **Open:** closed 2026-11-04: the monitor now ends a killed worker the schedd no longer holds (above).

## 2026-10-25: a failed schedd query no longer cancels workers (recorded 2026-10-30)

- **By:** ePIC production operations (swf-2), on Torre Wenaus's word ("INSTALL IT"), after an independent review (swf-3). Recorded here on 2026-10-30 by swf-1: the installation was recorded only in swf-epicprod `docs/HARVESTER_WORKER_STATE.md`.
- **Why:** after an HTCondor schedd outage on 2026-10-25, 348 active PanDA jobs were attached to workers recorded as cancelled. The HTCondor monitor turned a failed query into an empty result, and the monitor body turned repeated unknown results into cancellation.
- **What:** the three files above, from swf-epicprod commit e7d5eb9 (`scripts/prepare-harvester-monitor-safety.py`). The matching PanDA server change, refusing new dispatch to an ended worker, is in [panda-server/UPGRADE.md](../panda-server/UPGRADE.md) (Local changes on the host).
- **Installed:** 17:20:38 UTC, `panda_harvester-uwsgi` restarted; manifest `/opt/harvester/worker-safety-20261025T172038Z/installation.json` with each file's SHA-256 before and after. On 2026-10-30 all three files still match the manifest's `after` values.
- **Rollback:** restore the copies beside each file, suffix `.before-worker-safety-20261025T172038Z`, keeping owner and mode, then restart `panda_harvester-uwsgi`.

## 2026-10-28: pilot-log retention

- **By:** ePIC production operations (swf-1), on Torre Wenaus's word.
- **What:** at 00:46 ET a one-off pass gzipped the pilot logs idle 6 hours and
  not named by a queued job: 394,824 files, 447 GB before compression (list
  and log in `/var/log/epicprod-pilot-log-gzip/20261028T044649Z.*`). Then
  `pilot-log-retention.py` was installed with an hourly cron entry as
  `atlpan`: compress after 6 hours, remove hour directories after 6 days
  ([README.md](README.md#pilot-log-retention)).
- **Why:** `/var` was at 92%, 42 GB free of 520 GB; 437 GB of it was pilot
  logs back to 21 October, rotated by nothing.
- **Verified:** the installer's `--dry-run` as `atlpan`, then the first
  hourly run's line in `retention.log`.
- **Rollback:** `./install-pilot-log-retention.sh --remove` stops it;
  `gunzip` restores a compressed log. Removed logs are not recoverable.

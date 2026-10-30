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
| `harvestermonitor/htcondor_monitor.py` | worker safety: a failed schedd query leaves the batch's worker states unchanged and reports the failure, instead of an empty answer that reads every worker as missing; HTCondor workers of unknown state are kept past `checkTimeout`. Regulation: the condor-history age limit has a floor, `monitor.historyMaxAgeFloor` | 2026-10-25; 2026-10-22 | **outstanding**: no branch, no pull request |
| `harvesterbody/monitor.py` | worker safety: workers of a failed query keep their status, unchecked, with a `WORKER_STATE_UNVERIFIED` message; a worker of unknown state past `checkTimeout` is kept when the plugin sets `preserveUnknownWorkers`. Regulation: the FIFO check interval has a ceiling, `monitor.fifoMaxCheckInterval` | 2026-10-25; 2026-10-22 | **outstanding**: no branch, no pull request |
| `harvestermisc/htcondor_utils.py` | worker safety: a failed command-line query raises | 2026-10-25 | **outstanding**: no branch, no pull request |
| `harvesterbody/cacher.py` | regulation: a per-key refresh interval, `cacher.refreshSecondsByKey` (job statistics refreshed faster than the rest) | 2026-10-22 | **outstanding**: no branch, no pull request |
| `harvesterbody/worker_adjuster.py` | regulation: missing or stale job demand, older than `submitter.jobStatsMaxAge`, holds new pilot submissions (`REGULATION_HOLD`) | 2026-10-22 | **outstanding**: no branch, no pull request |
| `harvesterbody/propagator.py` | a PanDA kill command marks the job's workers to be killed after 600 seconds, so that HTCondor returns the pilot's stdout first; by PanDA operations at BNL, not recorded beyond the comment in the file | 2026-07-09 | not proposed; uses the existing `delay_seconds` of `mark_workers_to_kill_by_pandaid` |

The regulation changes of 2026-10-22 are installed by swf-epicprod `scripts/configure-osg-regulation.py` and described in swf-epicprod `docs/REGULATION_AUDIT_2026-10-22.md`; each reads a configuration value and does nothing when it is absent.

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

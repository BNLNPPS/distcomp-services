# PanDA server: change log

Every change to the PanDA server and JEDI installation on `pandaserver01.sdcc.bnl.gov`, newest first. An entry records the date, the role that made the change, what changed (package versions with commits, configuration files with the motivation), how it was verified, and the rollback copy. Upgrades follow [UPGRADE.md](UPGRADE.md).

## 2026-10-31: `panda_jedi` restarted after a worker ran out of file descriptors

- By: Claude swf-1, on Torre's approval (2026-10-31, 02:01 ET), at swf-watch's
  request under the standing service-recovery authority
  (swf-epicprod `docs/EPICPROD_OPS.md`, Torre, 25 October 2026).
- Why: JEDI stopped working at 00:42 UTC on 2026-10-31 (20:42 ET 10-30).
  `panda_jedi_stderr.log` at 00:42:19 UTC: `OSError: [Errno 24] Too many open
  files` in `multiprocessing/resource_sharer.py`; from then on every
  JediTaskBuffer call failed with "received 0 items of ancdata", the JEDI
  logs stopped at 00:44:17 UTC, and no managed job was created after
  00:33 UTC. The JediMaster processes were alive. JEDI worker 1149361 held
  1,021 descriptors of its 1,024 soft limit, 988 of them pipes; workers
  1149365, 1149355 and 1149364 held 917, 915 and 876. The processes had
  run since the nightly rotation restart at 07:43 UTC on 10-30, so the leak
  is about 1,000 pipes in 17 hours in some JEDI agent; which one is not yet
  known. The pressure front held every queue meanwhile (no verified
  throttler decision).
- Changed: `sudo systemctl restart panda_jedi` at 06:01:18 UTC. No file
  changed.
- Verified: `panda_jedi` active, `DB schema check: OK`, 27 JediMaster
  processes; JediDBProxy, JobGenerator, TaskRefiner, ContentsFeeder and
  EpicProdJobThrottler logs writing from 06:02 UTC; `REGULATION_OK vo=epic
  mode=throttle` at 06:02:18 UTC; no new stderr output. First new job
  6562827 (task 41494, NERSC_Perlmutter_epic_es) created 06:01:34 UTC; 932
  managed jobs created by 06:02:23 UTC, 924 of them for task 41631 at
  UM_GREX_PanDA_1.
- Open: find the leaking agent (descriptor counts per JediMaster process
  over the day) before the next rotation leaves it 17 hours to fill.

## 2026-10-29: a resume clears the paused superStatus (a local patch, on Torre's word)

- By: Claude swf-1, on Torre's word.
- Why: task 41525 ran with `superStatus` `paused` after its resume at 21:41 UTC,
  read as a sign the task was still paused. `getTasksToExecCommand_JEDI` carries
  out a resume as the status `dummy` (`commandStatusMap`: back to `oldStatus`),
  and its T_TASK and superStatus update tests the new status for running, ready
  or scouting after paused, so it never fired on a resume: that branch of the
  test was unreachable. A resumed task kept `paused` in both until its next
  status change. Dispatch was unaffected (the job dispatcher does not read the
  field; only the workflow step handler does).
- Changed: the update is judged on the status the task lands in
  (`actualNewStatus`, now computed before it), writing the values the existing
  branch was written to write. Only resume behaves differently: avalanche and
  release also map to `dummy` but set their own status or none
  ([patches/resume-superstatus](patches/resume-superstatus/)). Upstream master
  carries the same code.
- Installed 00:39:41 UTC on 2026-10-30, outside `host-install.py`: an ad hoc
  script with the same exactly-once match, the backup beside the file (suffix
  `.before-resume-superstatus-20261030T003941Z`, the name `host-install.py`
  gives) and a compile check; no `install.json` record. SHA-256 before
  `56e0b134…`, after `b4b557de…` (blob `f45dd897`). `prepare.py` with the patch's
  `edits.json` rebuilds the installed file byte for byte from the backup.
- Restarted `panda_jedi` at 00:39:58 UTC: active, JediMaster processes running,
  no error in the stdout log tail, `getTasksToExecCommand_JEDI` cycling at
  00:40:08 UTC.
- 41525 corrected after the restart with the server's own `setDeftStatus_JEDI`
  and `setSuperStatus_JEDI`, guarded on status `running` and superStatus
  `paused`: read back `running` / `running`.
- Audit after the install (`audit/`): eight files differ from `a754853d`, the
  seven listed before and this one; UPGRADE.md's table now lists it.
- Verified on 2026-10-30: task 41470's resume at 09:47:42 UTC wrote the DEFT status (`setDeftStatus_JEDI` in the JEDI log), which the unpatched path never did.
- Deviations from UPGRADE.md, Local changes on the host: installed without
  `host-install.py`, and PanDA operations at BNL were not notified before the
  install.
- Upstream: branch `epic-resume-superstatus` off PanDAWMS/panda-server master
  carries the identical change lines (checked against the live diff); not yet
  pushed; the pull request is to follow at Torre's word.
- Rollback: `host-install.py --bundle <bundle> --stamp 20261030T003941Z --rollback`
  from a bundle `prepare.py` builds from the backup, then restart `panda_jedi`.

## 2026-10-28: epic and legacy wlcg share production regulation

- By: Codex swf-teamcomms, on Torre's renewed instruction to finish the
  25 October epic-VO migration. Only the ePIC plugin package and its
  policy changed; panda-server source and PanDA HTTP were unchanged.
- Installed swf-epicprod cae1d52 as a wheel with `--no-deps
  --force-reinstall`; wheel SHA-256
  7844bff802a5ddb184b322c97117da973ea2fb1ef345e701a1d7d710581169f0.
  `pip check` passed. The shared throttler and existing EpicDDMClient
  imported successfully as atlpan.
- The throttler sums equivalent epic and wlcg queues, with one logical
  grant scope shared across VO names and resource types. Production,
  test and user queues retain separate scopes. Missing peer queues or
  failed statistics reads hold generation.
- Canonical epic POOLS now matches the current production policy:
  `osg:BNL_OSG_PanDA_1;osg_drain:BNL_OSG_EPIC_PROD_1`. The retired queue
  remains isolated. MODE stays throttle and the active OSG queued floor
  stays 3,123. The first SSH invocation lost the text after the semicolon;
  its nonzero result was detected and the complete value was reapplied
  and read back before installing the plugin.
- JEDI generation stopped at 20:00:12 UTC, resumed at 20:03:42 UTC after
  the old 180-second grant lifetime elapsed. Fresh `REGULATION_OK`
  records from both VOs show `accounting=epic+wlcg` and the identical
  managed scope `epic:queue:managed:managed`. JEDI is active. The
  existing ledger was retained.
- Preservation: /opt/panda-backup-20261028-epic-vo, a complete copy of
  /opt/panda taken before the install; the policy readback before the
  change is retained on swf-testbed under
  /data/wenauseic/pcs-operations/epic-vo-jedi-config-before.txt.
- Submission defaults and templates belong to the accompanying PCS
  cutover (swf-epicprod 237c069). A recovered test prematurely changed
  19 live templates at 19:59:18 UTC; original records 7150902–7150921
  (excluding 7150916) are retained, with corrective audit 7152516 naming
  the executor and the synthetic test identity. The templates remain at
  Torre's approved epic target. The tests now forbid database access,
  and the migration action checks administrator access in its body.
- Acceptance: task 41495 is done; job 6339107 finished at 20:43:14 UTC,
  VO epic, label managed, 100 events, no reported errors. It started at
  20:35:02 UTC, within one second of generation. FULL and RECO each
  registered one 100-event file, AVAILABLE at BNL-XRD (674,526 and
  2,638,652 bytes; Adler-32 3ac996bd and 7c4b16c9). The ordinary PanDA
  log is ready, 79,343 bytes. Exact trial identity and the 37 focused
  checks are in swf-epicprod/docs/EPIC_VO_MIGRATION.md. This is validation
  only, without additional campaign production credit.

## 2026-10-28: JEDI reads inputs from the catalog that holds them (swf_epicprod EpicDDMClient, on Torre's word)

- By: Claude swf-1, installed 18:34:24 UTC, `panda_jedi` restarted, active,
  DB schema check OK, seven JediMaster processes, no traceback in
  `panda_jedi_stderr.log`.
- Why: ePIC's inputs reside wherever their catalog says (Torre, 2026-10-28:
  "engineer, all the way down, inputs residing elsewhere"; "Rucio tells you
  where the data is"). The upstream DDM interface reads one catalog, PanDA's
  own, so an EVGEN input had to be copied to BNL and registered there.
- Changed: swf-epicprod `e9721a78` installed (wheel 0.3.0, `--no-deps
  --force-reinstall`, `pip check` clean). `panda_jedi.cfg` `[ddm]` line 79:
  `AtlasDDMClient` to `swf_epicprod.jedi.EpicDDMClient:EpicDDMClient` for `wlcg`
  and `epic`. New `/opt/panda/etc/panda/epic_catalogs.json` (atlpan, 600): the
  catalog map, `epic` scope names under `/` read from JLab's Rucio with its
  read account; every other DID on the server's catalog as before.
- Verified: gate `gate-a754853d` config load, 42 targets, 0 failed; read as
  atlpan on the host before the install, the eAg 9x115 x_1e-2to1e-1 sample's
  10 files with events, sizes, adler32 and stable GUIDs; after the restart
  the module logs `start EpicDDMClient` in each JEDI process. The
  ContentsFeeder's "failed to push trigger message" warnings predate the
  restart (108 and 109 in the ten minutes before it).
- 14:46 ET: the map's JLab entry names `vo: def`. Unnamed, the client took
  `vo = eic` from the server's `rucio.cfg` (read under JEDI's `VIRTUAL_ENV`)
  and JLab refused the read account ("Cannot authenticate"); canary 41489
  went pending at refinement on it. Backup
  `epic_catalogs.json-backup-20261028-vo`; no restart (the map is reread).
- 14:51 ET: swf-epicprod `a9cc04a2` reinstalled, the map's JLab entry marked
  `lfn_basename`, `panda_jedi` restarted (18:51:22 UTC, active, no traceback).
  JEDI's Event Service spec joins its fields with '/'; a JLab path name broke
  it, the job kept the raw spec in its 80-character `specialhandling` and
  `storeJobs` rolled back ("value too long for type character varying(80)",
  canary 41490). Files are now known to JEDI by the name's last component;
  canary 41491's job 6333770 stored with 6,000 event ranges. Backup
  `epic_catalogs.json-backup-20261028-basename`.
- 14:57 ET: swf-epicprod `7fc2ceb7` reinstalled, the map's JLab entry given
  `site_staged: ["NERSC_Perlmutter_epic_es"]`, `panda_jedi` restarted
  (18:57:44 UTC, active). Canary 41491's job stored but stayed `defined`:
  JEDI marks an input `ready`, and so activates the job, only for a file its
  DDM interface reports at the site, and JLab lists no replica at NERSC.
  Perlmutter stages a task's whole input at NERSC before the task is
  submitted, so a `site_staged` queue is reported holding the dataset's files
  on local disk. Canary 41492: broker `nFiles=1`, job 6334180 `activated`,
  input `ready`. Backup `epic_catalogs.json-backup-20261028-staged`.
- 16:21 ET: swf-epicprod `1ea34b38` installed, `panda_jedi` restarted
  (20:21:00 UTC): the DDM interface was to give a task's listing the task's
  own per-file event counts (`epicFileEvents`). It cannot: JEDI runs a DDM
  interface in a process of its own and sends it the dataset name only, so
  canary 41496 kept the catalog's counts (one record, run001's first 50,000
  events; run003 dropped). 16:25 ET: swf-epicprod `d10f0925` installed in its
  place, the lookup removed, `panda_jedi` restarted (20:25:03 UTC, active).
- 20:00 ET: the map's JLab entry `site_staged` gains `BNL_ePIC_GOOGLE_es`
  (Google stages a task's EVGEN input in its cluster's bucket before the task
  starts, swf-epicprod docs/GKE_PILOT_FLOW.md, EVGEN input); the interface
  rereads the map when it changes, no restart. Backup
  `epic_catalogs.json-backup-20261028-google`.
- Rollback: `/opt/panda-backup-20261028-epicddm` holds the previous
  `swf_epicprod` package and `panda_jedi.cfg`; the live file's backup is
  `panda_jedi.cfg-backup-20261028-epicddm`. Restore the line, reinstall the
  saved package, restart `panda_jedi`.

## 2026-10-28: the event API log rotates by size, hourly, without a restart (on Torre's word)

- By: Claude swf-1.
- Why: `panda-api_event.log` is written at DEBUG (global `log_level`) and grew
  about 5.8 GB a day with one Perlmutter node and Google on 10-event ranges,
  against 16 GB free on `/var`; the package's daily rotation is the only one
  and restarts PanDA. Five Perlmutter nodes would fill `/var` between nights.
- Changed: `/etc/panda/panda-api-event.logrotate` rotates that log alone past
  2 GB with `copytruncate`, compressed into `/var/log/panda/api_event/`, kept six
  days; `/etc/cron.d/panda-api-event-logrotate` runs it hourly with its own state
  file ([api-event-logrotate](api-event-logrotate/README.md)). No PanDA
  configuration, level or restart changes; the daily entry is unchanged.
- Verified: logrotate's dry run at install, then the first size rotation.
- Rollback: `api-event-logrotate/install.sh --remove`.

## 2026-10-27: the job event count adds each call's finished ranges (a local patch, on Torre's word)

- By: Claude swf-1, installed 16:46:13 UTC, `panda_httpd` restarted, active,
  `is_alive` 200. Torre preferred this form: range updates are the most
  scaling-sensitive path in PanDA, and this one adds no query to it.
- Why: the rollback below brought back the `:PandaID` KeyError it was meant to
  fix; a rollback is not a repair. The recount of the job's finished ranges
  that the bind fix enabled walks every range of a fine-grained job on every
  call. Restricting it to the call's own ranges was measured on a live job of
  426,496 ranges and still took 325 ms for 1,000 keys: the planner filters the
  keys instead of looking each one up.
- Changed: `updateEventRanges` adds to the job's `nEvents` the ranges the call
  reports finished times the events per range (`SET nEvents=COALESCE(nEvents,0)+:nEvents`),
  with no query of `JEDI_Events`
  ([patches/event-count-incremental](patches/event-count-incremental/)). A
  call repeated after a lost answer adds its ranges again; the pilot's own
  updates and the close-out set the count outright.
- Rollback: `host-install.py --bundle <bundle> --stamp 20261027T1650Z --rollback`.

## 2026-10-27: event-count patch rolled back (range updates slowed to seconds)

- By: Claude swf-1, at 16:37:39 UTC, as repair of the change below.
- Why: with the bind fixed, the statement ran for the first time: it recounts
  the job's finished ranges in `JEDI_Events` on every range update. The plan is
  an index scan on the job's key, filtered by status, so the count walks every
  range of the job; fine-grained jobs hold up to millions. Range updates took up
  to 5 to 8 s each from 16:17 UTC, against about 0.6 s for a 2,000-range report
  before.
- Changed: `host-install.py --rollback` restored the file with the fine-grained
  patch alone (blob `db1563ee`); `panda_httpd` restarted, active, `is_alive` 200.
  The KeyError and the static job event count return.
- Next: an event count that adds the ranges a call finishes instead of
  recounting the job's ranges.

## 2026-10-27: the job event count of Event Service jobs updates again (a local patch, on Torre's word)

- By: Claude swf-1, on Torre's word ("must be fixed").
- Why: `updateEventRanges` commits a job's range updates, then sets the job's
  `nEvents` from its finished ranges. That statement's subquery named
  `:PandaID` while its parameters, as everywhere in the module, carry
  `:pandaID`; PanDA's PostgreSQL cursor matches names exactly, so it raised
  `KeyError ':PandaID is missing in SQL parameters'` on every update (5,616 on
  10/26, 14,274 in all retained logs), the job's `nEvents` never moved, and each
  answer carried a trailing `False`. The batch pilot accepts the answer with or
  without it.
- Changed: the one bind, `:PandaID` to `:pandaID`, in `task_event_module.py`
  (blob `a70df524`), prepared from the installed file with
  [patches/prepare.py](patches/prepare.py) and
  [patches/event-count-bind/edits.json](patches/event-count-bind/edits.json) and
  installed with [patches/host-install.py](patches/host-install.py). Record
  `/opt/panda/event-count-bind-20261027T1630Z/install.json`; backup beside the
  file, suffix `.before-event-count-bind-20261027T1630Z`.
- Restarted `panda_httpd` at 16:17:32 UTC: active, `is_alive` 200; no
  `missing in SQL parameters` error since.
- Audit: the retained logs hold no other missing-bind error. A scan of the code
  for bind names that differ from their parameter keys only in case finds one
  more, in the HPO path of `_check_task_with_unprocessed_inputs`
  (`task_complex_module.py`, `:taskid` against `:taskID`), which ePIC does not
  run; it goes to the maintainers with this fix.
- Rollback: `host-install.py --bundle <bundle> --stamp 20261027T1630Z --rollback`,
  then restart `panda_httpd`.

## 2026-10-27: duplicate Harvester_Workers rows removed

- By: Claude swf-1, on Torre's word ("that must be fixed").
- Why: the Perlmutter harvester reported "failed to update workers with database
  error in the PanDA server" every 30 minutes. `updateWorkers` sets `lastUpdate`
  on every row of a worker, the date-partitioned table moves them into the day's
  partition, and two rows of one worker collide on its key: UniqueViolation on
  `harvester_workers_p20261027_pkey`, and the whole batch rolls back. Workers
  18104 (2 rows) and 18253 (4 rows) of `Perlmutter_test_1`, from 2026-08-20 and
  21, and worker 0 of `BNL_harvester_1` (4 rows, 2026-10-19) had copies written
  within milliseconds of each other.
- Changed: [dedupe_harvester_workers.py](dedupe_harvester_workers.py) deleted the
  7 extra rows, keeping each worker's newest, in one transaction through the
  parent table (the database account may not delete from a partition directly).
  No duplicated worker remains.
- Rollback: none needed; the deleted rows were copies of the rows kept.

## 2026-10-27: fine-grained Event Service ranges of several events (a local patch, on Torre's word)

- By: Claude swf-1, on Torre's word to patch the server ahead of an upstream
  release. PanDA operations at BNL were notified before the install.
- Why: JEDI gives a fine-grained task single-event ranges (`JobGenerator.py`),
  and inserting a job writes one `JEDI_Events` row per unprocessed event in one
  transaction, inside JEDI's fixed 600 s limit on `storeJobs`. A 6M-event first
  job took 563 to 596 s; the retry of task 41316 (5,750,520 ranges) timed out,
  was rolled back and was repeated every ten minutes from 2026-10-26 19:27 UTC.
- Changed: a task parameter, `nEventsPerFineGrainedRange` (split rule `FR`),
  sets a fine-grained task's events per range; a task without it is unchanged.
  Five files: `task_split_rules.py`, `JediTaskSpec.py`, `TaskRefinerBase.py`,
  `JobGenerator.py`, `task_event_module.py` (the job's event count multiplies
  finished ranges by the range size). Prepared from the installed files and
  installed file by file with [patches/fine-grained-range-size](patches/fine-grained-range-size/);
  the change lines are identical to branch `fine-grained-range-size` off
  PanDAWMS/panda-server master.
- Before the install the installed tree was compared with its commit `a754853d`
  ([audit/](audit/)): 420 files, two differing, both listed in UPGRADE.md (Local
  changes on the host) and untouched; the five files read their `a754853d`
  content.
- Checks of the branch: pre-commit 4.6.2 over the tree (ruff, ruff-format,
  mypy, the slots import) passed; 283 unit tests on the branch and on master,
  the same 63 failures on both (62 `api/v1` tests that call the live CERN
  server, one `key_reads_tests` case).
- Installed 14:26 UTC. Record `/opt/panda/fine-grained-range-20261027T1430Z/install.json`
  (SHA-256 before and after); backups beside each file, suffix
  `.before-fine-grained-range-20261027T1430Z`.
- Restarted `panda_jedi` and `panda_httpd` at 14:26:42 UTC: five services
  active, JEDI's `DB schema check: OK`, `is_alive` 200, no traceback in the JEDI
  or daemon stderr logs or the server error log, the job generator cycling.
- Not yet verified: a task carrying `nEventsPerFineGrainedRange`.
- The fork build branch `epic-container-image-dispatch-725129f3` now carries
  upstream master's `setupper_dummy_plugin.py` (b62aa5b5), the installed
  version, so an install from it no longer reverts that file.
- Rollback: `host-install.py --bundle <bundle> --stamp 20261027T1430Z --rollback`
  (each file must read its installed checksum; the backups are restored), then
  restart `panda_jedi` and `panda_httpd`.

## 2026-10-26: BNL_ePIC_GOOGLE_es maxtime 999999999 in the server's queue record

- By: Claude swf-2, within Torre's direction of the Google Event Service work.
  swf-epicprod 950f475 (`pandaserver/schedconfig-overrides.json`,
  docs/SCHEDCONFIG_OVERRIDES.md); no file on this host was edited by hand.
- Why: JEDI's scouting divides a job's wall time by its input size; a
  particle-gun ES task's input is a few-kB generation plan, so the task
  walltime reaches JEDI's cap, 999999999 kSI2kseconds (task_utils_module.py).
  GenJobBroker skips any queue whose maxtime is lower, so a file left by a
  partial job never got its next consumer: task 41223's 10,576 events stood
  "no candidates" at maxtime 345600. The queue's pods have no wall clock; the
  harness deadline bounds each job, and the pilot's limit comes from its own
  queue file.
- Verified: the 5-minute sync wrote revision 1c498cf
  (`schedconfig.json.provenance.json`), and the server's `schedconfig_json` row
  for BNL_ePIC_GOOGLE_es read maxtime 999999999 at 11:10 UTC.
- Rollback: remove the BNL_ePIC_GOOGLE_es entry from the overrides file on
  swf-epicprod main; the next sync restores CRIC's 345600.

## 2026-10-25: refuse dispatch to terminal worker parents

- By: Codex swf-2, on Torre's direct "INSTALL IT", after swf-3's independent
  review and 13 focused captured-source regression checks. Source preparation:
  swf-epicprod e7d5eb9. This is an operator-authorized local patch, separate from
  the installed image filter and from any VO migration.
- Changed only job_complex_module.py in the installed DB proxy modules. getJobs
  locks an existing worker parent before candidate mutation and refuses a
  finished, failed, cancelled or missed parent. Existing job completion and output
  registration paths are unchanged; terminal worker records were not revived.
- Input SHA-256 8712b38e8bc1e85ff99014f973f48b548959b3f1f811e517eab89a1d337c5bf7;
  installed SHA-256 3624cfeb008599ca2ade456e18dea76fad79ad87aa10da9f728cb68fde0be966.
  Backup beside the module: job_complex_module.py.before-worker-safety-20261025T172111Z.
  Full installation audit: /opt/panda/worker-safety-20261025T172111Z/installation.json.
- Restarted only panda_httpd, active at 17:21:32 UTC. API is_alive returned 200.
  A 17:23:24 UTC central query found 55 newly started OSG jobs since activation
  (52 running, two starting, one sent), all attached to running worker parents.
  No natural terminal-parent refusal appeared in the initial sampled log tail;
  the refusal path is covered by the focused regressions, not claimed witnessed
  in production. Harvester's matching uncertainty safeguards were activated
  separately on osgsub01 at 17:20:54 UTC.
- Rollback: restore the exact dated module copy, retaining ownership and mode,
  then restart only panda_httpd. Package versions, schema, configuration,
  JEDI and daemon services were unchanged. An upstream upgrade must preserve or
  replace this patch until upstream integration is resolved.

## 2026-10-24: BNL_OSG_PanDA_1 maxtime 16 hours (swf-epicprod 9fa361f)

- `pandaserver/schedconfig-overrides.json`: `maxtime` 57600 for BNL_OSG_PanDA_1 (was 36000), on Torre's go, applied by the five-minute writer on both hosts. Motivation: FSU's slots run some 41052 rows past ten hours (five jobs killed at 591 minutes by the ten-hour limit, 2026-10-24 08:20Z) and FSU's glideins have 29 to 47 hours left. maxtime is the pilot's job limit for the whole queue; the per-site batch limit (the native launcher, swf-3) holds every other site at ten hours.
- Rollback: set `maxtime` back to 36000 through a commit to swf-epicprod main.

## 2026-10-23: BNL_OSG_PanDA_1 maxtime 10 hours (swf-epicprod 4a2f92d)

- By: swf-2 (Claude Code), on Torre's order ("FIX THE KILL tiME").
- `pandaserver/schedconfig-overrides.json`: `maxtime` 36000 for BNL_OSG_PanDA_1 (was CRIC's 21600), applied by the five-minute writer on both hosts. Motivation: direct pilots reach slow OSPool slots; at SU-ITS 41043 jobs took 269 to 339 minutes against about 128 elsewhere, and job 5816718 was cut at 359 minutes. The submit description's own runtime limit (`+MaxRuntime 360`) is raised separately on osgsub01.
- Rollback: remove the `maxtime` key through a commit to swf-epicprod main; the next writer run restores CRIC's value.

## 2026-10-23: panda-server a754853d, image-aware job dispatch (a local patch, on Torre's word)

- By: swf-2 (Claude Code). Torre: "WE PATCH PANDA. EVALUATE. IF ALL OK SEND A PR UPSTREAM AND RESYNC." This is the one exception to the rule below that the server runs no local patch (UPGRADE.md, ePIC modules in JEDI).
- Installed panda-server `a754853d` from the fork `wenaus/panda-server` (branch `epic-container-image-dispatch-725129f3`): the installed commit 725129f3 plus an optional `container_name` argument on `acquire_jobs`, which adds `container_name = :containerName` to the job selection so a pilot bound to one container image acquires only jobs that run in it. Without the argument nothing changes. `pip install --no-deps --force-reinstall` of panda-server only; `pip check` clean; the freeze differs only in the panda-server line; units and templates identical to the backup. The three changed files were verified byte-identical to 725129f3 before the install.
- Evaluation: unit tests (3/3 under `/opt/panda/bin/python`), the integrity gate on pandaserver02 (`gate-a754853d`: 298 modules, only the four known failures; 42 configured targets plus the ePIC throttler and adder plugins load), and an audit by swf-3 (API boundary, retry path, callers, live read-only query plans 10 to 18 ms).
- Restarted only `panda_httpd` at 15:34:49 UTC; `is_alive` 200, every request since 200, no tracebacks. The daemon and JEDI load the code at the nightly rotation; their paths are unchanged.
- Verified in production 16:07 to 16:41 UTC: pilots declaring `eic_xl:26.07.3-stable` received "No jobs in PanDA" against 3,196 queued 26.07.1 jobs; pilots declaring 26.07.1 finished trial jobs 5856208, 5856308 and 5856309 with output and logs registered. OSG production pilots declare their image from Condor cluster 27675 (16:41:54 UTC).
- Backup: `/opt/panda-backup-2026-10-23`. Rollback: pilots first stop sending `container_name` (an unpatched server rejects the argument), then the UPGRADE.md rollback from the backup. The upstream pull request (branch `container-image-dispatch`) follows three hours of production, at Torre's word; once merged, the server resyncs to an upstream commit.

## 2026-10-22: ePIC adder skips absent and failed files

- By: Codex swf-3, on Torre's instruction to use an ePIC-owned plugin.
- Installed swf-epicprod `0ae45ae` from its wheel with `--no-deps --no-index --force-reinstall`. The separate `swf_epicprod.panda.EpicAdderPlugin` subclasses the upstream simple adder and excludes `nooutput` and `failed` files during registration, restoring the original file list afterward. PanDA core source was unchanged; the installed simple-adder checksum was verified unchanged. The installed ePIC JEDI sources were also unchanged and `pip check` passed.
- `configure_epic_adder.py` changed only `adder_plugins` in `/opt/panda/etc/panda/panda_server.cfg` to `wlcg:swf_epicprod.panda.EpicAdderPlugin:EpicAdderPlugin,epic:swf_epicprod.panda.EpicAdderPlugin:EpicAdderPlugin`. Backup: `panda_server.cfg.before-epic-adder-20261022T223415Z`; prior ePIC package: `/opt/panda/swf_epicprod.before-adder-0ae45ae`.
- Before restart, `gate/adder_nooutput.py` passed with actual PanDA JobSpec/FileSpec objects and mocked Rucio calls, and `gate/epic_adder_config.py` confirmed both configured VOs through the actual adder entry point. Four local boundary tests covered file restoration and preservation of upstream errors.
- Restarted only `panda_daemon`, active at 22:34:42 UTC. Fresh job 5805903 of task 41039 finished with `logHeld=s3` and DDM error 0 at 22:34:57. By 22:38 UTC, 109 jobs from 41039/41040 had finished since restart, with no new DDM collision. One separate failure had DDM error 0. Historical failed jobs and catalog records were not rewritten.
- To reverse plugin selection, restore the saved configuration and restart only `panda_daemon`. This restores the old registration behavior, including its absent-file defect. PanDA maintainers have the generic correction separately as [PR 836](https://github.com/PanDAWMS/panda-server/pull/836).

## 2026-10-22: isolate retired PROD_1 stock from active OSG generation

- By: Codex swf-3, restoring OSG supply and moving the remaining PROD_1 tasks on Torre's instruction.
- At 22:16 UTC, changed the `wlcg` JEDI `epic_job_throttler` `POOLS` row from `osg:BNL_OSG_PanDA_1,BNL_OSG_EPIC_PROD_1` to `osg:BNL_OSG_PanDA_1;osg_drain:BNL_OSG_EPIC_PROD_1`, using swf-epicprod `scripts/jedi-throttler-config.sh`. Modes and limits were unchanged. The retired queue's large stock had excluded both queues from generation while the active queue had only about 240 activated jobs.
- The 22:18:11 UTC JEDI decision gave active OSG room for 2,930 jobs and excluded the drain independently. Active OSG reached 3,192 activated jobs at 22:26 UTC. Harvester reached its configured 600 waiting pilots at 22:20:36 and submitted replacements on the next cycle. No service restart was required.
- Prior value is recorded above; restore it only through the same configuration script after checking that a retired backlog cannot starve the active queue again. The `epic` test-VO row was not changed.


## 2026-10-22: verified JEDI regulation and synchronized queue resources

- By: Codex swf-3, implementing Torre's accepted regulation audit with explicit authorization to complete deployment while he was AFK.
- Installed swf-epicprod code `ffd9fdf` from a locally built wheel, `pip install --no-deps --force-reinstall`; `pip check` passed. JEDI restarted and active at 04:56:27 UTC. Backup: `/opt/panda/swf_epicprod.before-regulation-20261022`.
- The throttler now reserves grants atomically under a process-shared lock, with VO/work-queue scopes. Missing/invalid mode, corrupt ledger, or missing generation-lock/site-exclusion support holds generation. Both VOs emit fresh `REGULATION_OK`; the server reporter 1.1 carries it to the front. Both MODE rows remain `throttle`.
- `/opt/panda/etc/panda/schedconfig/panda-schedconfig.py` and its five-minute cron now resolve GitHub main and fetch the override file at that immutable commit. Both harvesters do the same. The sidecar `schedconfig.json.provenance.json` records revision and hashes. All three manual installs and the 05:00 UTC cron runs produced identical input and output hashes from `6671257`. Source failures retain last-good records.
- GREX records one core, 6000 MB, 18000 seconds and timefloor 180 per pilot, distinct from its fixed eight-core/48000 MB allocation. Both OSG queues record one core and 4096 MB; osgsub01's new pilots now request 4096 MB too. OSG timefloor remains 120. The configurator's live records verified these resource limits.
- Rollback: stop JEDI, restore its `swf_epicprod/jedi` directory from the backup, restart JEDI. Restore static overrides through a repository revert; merely editing a synchronized local file is undone by the next cron run. Dated writer/cron/config backups are beside their originals. The complete scope, evidence, tradeoffs and Harvester rollback are in [the implementation report](https://github.com/BNLNPPS/swf-epicprod/blob/main/docs/REGULATION_AUDIT_2026-10-22.md).

## 2026-10-21: BNL_OSG_PanDA_1 recorded as 1 core, 4096 MB (swf-epicprod 09da46a)

- By: the ePIC production operators (Torre Wenaus with an AI session), 17:35 ET
- Overrides from swf-epicprod 09da46a on both hosts (`COMMIT` updated; backups `schedconfig-overrides.json-backup-2026-10-21b`): `corecount` 1 and `maxrss` 4096 for BNL_OSG_PanDA_1 (CRIC: 8 and 48000). Motivation: the pilots are single-core and ask the pool for 3,700 MB, while the front's fit check and PCS readiness read this record, so the 5,400 MB eAu tasks 40856 and 40857 passed as fitting OSG and lost 55,824 jobs to memory kills on the two OSG queues in three days. 4096 is the default task declaration, which runs there. JEDI's GenJobBroker skips its memory check for a task whose site is set, so placed tasks are unaffected. BNL_OSG_EPIC_PROD_1 is unchanged.
- pandaharvester01: `schedconfig.log` had been owned by root since the 2026-10-20 install, so the writer's five-minute cron, which runs as atlpan, failed at every run, and the file was rewritten only by hand. Owner set to atlpan.
- Verified: both writers report `BNL_OSG_PanDA_1 corecount: 8 -> 1; maxrss: 48000 -> 4096`; the server's cache serves `corecount` 1 and `maxrss` 4096 for BNL_OSG_PanDA_1 from 17:40 ET, and BNL_OSG_EPIC_PROD_1's record unchanged.
- Rollback: the overrides at bc88329 (the backups) and the next writer run.

## 2026-10-21: OSG pilots take jobs for 120 minutes (timefloor; swf-epicprod bc88329)

- By: the ePIC production operators (Torre Wenaus with an AI session), 16:22 ET
- Overrides from swf-epicprod bc88329 on both hosts (`COMMIT` updated): `timefloor` 120 for BNL_OSG_PanDA_1 and BNL_OSG_EPIC_PROD_1 (was 0). Motivation: with 0 every pilot ran one job and left (994 jobs on 994 pilots in two hours at BNL_OSG_EPIC_PROD_1), so a queue ran only while a batch of its pilots stood at the front of the shared pool's line, and BNL_OSG_EPIC_PROD_1 fell to 0 running with 8,998 jobs queued. The pilot wrapper reads the field from this server's cache.
- Verified: `/cache/schedconfig/<queue>.all.json` serves `timefloor` 120 and `workflow` pull for both queues at 16:25 ET.
- Rollback: the overrides at b631c7c and the next writer run.

## 2026-10-21: BNL_OSG_PanDA_1 and BNL_OSG_EPIC_PROD_1 recorded as pull (swf-epicprod b631c7c)

- By: the ePIC production operators (Torre Wenaus with an AI session), 16:19 ET
- `/opt/panda/etc/panda/schedconfig/` and pandaharvester01 `/data/atlpan/harvester_common/schedconfig/`: overrides from swf-epicprod b631c7c (`COMMIT` updated; backups `schedconfig-overrides.json-backup-2026-10-21`), adding `workflow` `pull` for both OSG queues. Motivation: harvester on osgsub01 runs their pilots in pull mode since 2026-10-19, while the records said push, which put them under the server's meanRSS guard for push queues.
- Verified: the writer, run once on each host, wrote 103 queues with both OSG queues `push` to `pull`; `schedconfig_json` reads `pull` for both.
- Rollback: the overrides at 0c24fd1 and the next writer run.

## 2026-10-21: one throttler reading for the OSG pool; the epic VO throttles; 500 dead GREX jobs cancelled (swf-epicprod cc7d80e); JEDI restarted

- By: the ePIC production operators (Torre Wenaus with an AI session), 15:20 to 15:30 ET
- swf-epicprod e708437 to cc7d80e, `pip install --no-deps --force-reinstall`; `pip check` clean. Motivation: BNL_OSG_PanDA_1 and BNL_OSG_EPIC_PROD_1 feed one OSG pool but were read per queue, each with its own floor (3,123 and the default 2,000) and its own share of the running count, so the pool's allowance was the sum: 20,030 queued against 1,121 running that afternoon. A `POOLS` row now names the queues of a pool; the pool is one reading over their summed counts, held to the pool's limits, its queues excluded or granted together (swf-epicprod docs/EPIC_JOB_THROTTLER.md).
- `DOMA_PANDA.config`, with swf-epicprod `scripts/jedi-throttler-config.sh`: rows `POOLS` = `osg:BNL_OSG_PanDA_1,BNL_OSG_EPIC_PROD_1` and `NQUEUELIMIT_osg` = 3123 for both VOs (new). With `scripts/jedi-throttler-mode.sh`: the epic `MODE` row from `observe` to `throttle`, left at observe when wlcg was switched on 2026-10-20; epic tasks all run in the `test` work queue, read on its own, so production saturation does not hold canaries.
- 500 jobs of task 40855 at UM_GREX_PanDA_1 cancelled with `Client.killJobs` (all accepted): attempt 3, fetched in push mode on 2026-10-19 just before GREX went to pull, held by no pilot or batch job since 22:05 UTC that day. The throttler counts `starting` as running, so they raised GREX's bound by about 1,000.
- `sudo systemctl restart panda_jedi` at 15:27 ET.
- Verified: `engine up` at 19:28:04 UTC; first decisions `osg (BNL_OSG_EPIC_PROD_1+BNL_OSG_PanDA_1): SATURATED queued 19538+0 granted > max(2.0 x running 1074, NQUEUELIMIT 3123)` and `UM_GREX_PanDA_1: SATURATED queued 10285 ... running=847`; epic passes decided (`epic:any ... queue=test ... unthrottled: max_num_jobs=300`); 40855's 500 jobs `cancelled`.
- Rollback: `pip install --no-deps --force-reinstall` at e708437 and the same restart; the epic MODE row back to `observe`; the new rows are ignored by the earlier engine.

## 2026-10-21: JEDI generation lock for the ePIC VOs; job throttler excludes full sites (swf-epicprod e708437); JEDI restarted

- By: the ePIC production operators (Torre Wenaus with an AI session), 14:15 to 14:21 ET
- `panda_jedi.cfg` `[jobgen]`: `lockProcess = wlcg|epic:any:any:any` (none before; backup `panda_jedi.cfg-backup-2026-10-21`). Motivation: the job generator skips a throttled work queue only when it holds the process lock, and takes the lock only for the VOs this key names, so with the key absent the ePIC job throttler's "throttled" answer was ignored and the pass ran uncapped, kept only off the sites it named. At 12:12 ET UM_GREX_PanDA_1 read room 0 (queued 2,814 of 2,814), was not named, and the generator made 4,999 jobs for each of tasks 40856 and 40857 against a bound of about 2,800; BNL_OSG_EPIC_PROD_1's two new tasks were generated whole (9,998 jobs) the same way.
- swf-epicprod 9a7aab3 to e708437, `pip install --no-deps --force-reinstall`; `pip check` clean: a site with no room is named with the saturated sites (swf-epicprod docs/EPIC_JOB_THROTTLER.md).
- `sudo systemctl restart panda_jedi` at 14:19 ET.
- Verified: `panda_jedi` active; `engine up: exclusion_honored=True` per VO; first production decisions `SKIP throttled: excluded ['BNL_OSG_EPIC_PROD_1', 'BNL_OSG_PanDA_1', 'UM_GREX_PanDA_1']`; generator locks held by the `-gen` processes in `JEDI_Process_Lock` for wlcg and epic (nine sampled in a minute).
- Rollback: restore `panda_jedi.cfg-backup-2026-10-21`, `pip install --no-deps --force-reinstall` at 9a7aab3, and the same restart.

## 2026-10-20: queue JLAB_PanDA_1, defined by our overrides

- By: the ePIC production operators (Torre Wenaus with an AI session), 16:45 ET
- `/opt/panda/etc/panda/schedconfig/`: swf-epicprod 0c24fd1 installed (script and overrides; `COMMIT` updated). The writer now defines a queue CRIC does not have from `_clone`, a copy of a named queue's record with its own fields set (docs/SCHEDCONFIG_OVERRIDES.md). First such queue: `JLAB_PanDA_1`, cloned from UM_GREX_PanDA_1, with JLab's names, the HTCondor-CE `osg-ce-2.jlab.org:9619`, `status` `brokeroff`, `corecount` 1, `maxrss` 6000, `maxtime` 86400, storage BNL_PROD_DISK_1 as GREX. Motivation: JLab's CE accepts our pilots' token since 2026-10-20 (Kurt Strosahl, epic-prod-ops), and the queue was not to wait for a CRIC entry. JLab's glidein slots in the OSG pool run only CLAS12 (their START requires `projectName` clas12), so this is ePIC's only route to the JLab farm. `brokeroff` keeps brokerage off it: only jobs we place run there.
- Same day on pandaharvester01 (not this host): the same writer and overrides under `/data/atlpan/harvester_common/schedconfig/` with a five-minute cron, harvester's `panda_queues.json` cache read from that file instead of CRIC (`panda_harvester.cfg`, backup `-backup-2026-10-20`), and a `JLAB_PanDA_1` pull queue with single-pilot slots (swf-epicprod docs/SCHEDCONFIG_OVERRIDES.md, On the submit host).
- Verified: the writer wrote 103 queues (CRIC's 102 and JLAB_PanDA_1); the server's cache serves `/cache/schedconfig/JLAB_PanDA_1.all.json` (brokeroff, pull, CE osg-ce-2.jlab.org:9619, maxtime 86400) from 20:49 UTC.
- Rollback: set the harvester queue offline, then remove the `JLAB_PanDA_1` entry from the overrides (a commit, installed here and on pandaharvester01); the server drops the record at its next refresh.

## 2026-10-20: ePIC job throttler to throttle for production

- By: the ePIC production operators (Torre Wenaus with an AI session), 13:35 ET
- `DOMA_PANDA.config`: the wlcg `MODE` row set from `observe` to `throttle` at 17:35:59 UTC with swf-epicprod `scripts/jedi-throttler-mode.sh`; the engine is unchanged (swf-epicprod 9a7aab3, installed 2026-10-05). Motivation: in `observe` the engine read BNL_OSG_PanDA_1 as saturated (14,630 queued against max(2 × 271 running, `NQUEUELIMIT` 3,123)) and still passed every pass unthrottled, so a placed task had all its jobs generated at once: task 40857 had 47,845 jobs generated for BNL_OSG_EPIC_PROD_1, and its move to UM_GREX_PanDA_1 the same day left 43,026 queued jobs to kill, one at a time (each kill locks the task's JEDI dataset row). Both reasons the mode went back to `observe` on 2026-10-05 were fixed in that day's engine (the work-queue hold rule off; a starting job counted as running).
- Verified: the last `OBSERVE would` line for wlcg was at 17:36:54 UTC, as the JEDI processes reread the row. Since then production passes go unthrottled at 300 jobs with the saturated BNL_OSG_PanDA_1 and UM_GREX_PanDA_1 excluded, and BNL_OSG_EPIC_PROD_1 open with room 2,000 (`panda-EpicProdJobThrottler.log`).
- Rollback: the same script with `wlcg observe`.

## 2026-10-20: queue records from CRIC with tracked overrides

- By: the ePIC production operators (Torre Wenaus with an AI session), 12:11 to 12:12 ET
- The server's queue records now come from a file we write instead of from CRIC directly: CRIC's records with the overrides tracked in swf-epicprod (`pandaserver/schedconfig-overrides.json`, written by `scripts/panda-schedconfig.py`, docs/SCHEDCONFIG_OVERRIDES.md). Installed from swf-epicprod 15461fc into `/opt/panda/etc/panda/schedconfig/` (owner `atlpan`; `COMMIT` names the commit); `/etc/cron.d/panda-schedconfig` rewrites the file as `atlpan` every five minutes, log `/var/log/panda/panda-schedconfig-overrides.log`. When CRIC cannot be read the file is left as it is, so the server keeps its last records.
- `panda_server.cfg`: `CRIC_URL_SCHEDCONFIG` set to `/opt/panda/etc/panda/schedconfig/schedconfig.json`, the CRIC URL kept beside it as a comment (backup `panda_server.cfg-backup-2026-10-20`); `panda_daemon` restarted so the configurator daemons read it.
- First override: UM_GREX_PanDA_1 `workflow` `pull`. Motivation: GREX runs pull pilots since 2026-10-19, but recorded as push it fell under the dispatcher's meanRSS guard (`meanrss` 4000): with its running eAu jobs averaging about 5.7 GB, the server answered every GREX pilot "No jobs in PanDA" and held 10,125 activated eAu retries at 5,400 MB (`getJobs ... meanRSS will be throttled to jobs under 4000MB` in `panda-DBProxy.log`); GREX's running jobs fell from about 940 to 375.
- Verified: the first run wrote 102 queues with UM_GREX_PanDA_1 `push` to `pull`; the `schedconfig_json` daemon loaded it at 16:12:37 UTC; the dispatcher's last meanRSS hold for GREX was at 16:12:36 UTC (20,217 that day) and none since; GREX's running eAu jobs rose and its activated ones fell from the first half minute.
- Rollback: restore `panda_server.cfg-backup-2026-10-20` and restart `panda_daemon`; remove `/etc/cron.d/panda-schedconfig`.

## 2026-10-20: token clients for JLab Rucio and storage

- By: the ePIC production operators (Torre Wenaus with an AI session), 11:58 ET
- `/opt/panda/etc/panda/token_cache_config.json` created (owner `atlpan`, mode 600; the default path of `token_cache_config`, so `panda_server.cfg` is unchanged), with the two CILogon clients registered at JLab for the payload's token writes: `rucio` (audience `rucio-server.jlab.org`, scope `rucio`, prefetched by the token-cache daemon every 10 minutes) and `storage` (audience and path-scoped scope from each request). The client entries are as the JLab Rucio service sent them, plus `allowed_scope_verbs` `storage.read`, `storage.create`, `storage.modify` on `storage`: the stash copy overwrites (`storage.modify`), which the default verbs refuse. Motivation: the entry below; the patched server had no clients configured, so it issued no token.
- `panda_httpd` reloaded gracefully (SIGUSR1 to the main process) so the token endpoint reads the file; the server answered normally throughout.
- Verified: as `iddssv1` with the robot proxy, a `storage` request for audience `epicxrd1.sdcc.bnl.gov` and scope `storage.create:/eic/EPIC/TEST/canary/tokencheck` returned a token issued by `https://cilogon.org/jlab` with exactly that audience and scope.
- Rollback: remove the file and reload `panda_httpd` the same way.

## 2026-10-20: token permission for the pilots' robot identity

- By: the ePIC production operators (Torre Wenaus with an AI session)
- `DOMA_PANDAMETA.users`: one row added, as the server adds users (`users_id_seq`): id 17, name `iddssv1`, DN `/DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=iddssv1/CN=663551/CN=Robot: IDDS Server1`, `gridpref` `p`. Motivation: the JLab `eicprod` certificate the payload writes with expires 2026-10-28. Its replacement has the payload ask this server for Rucio and storage tokens (`/api/v1/creds/get_access_token`, the token patch installed 2026-10-09), signing in with the pilot's proxy, harvester's robot credential, since the pilots carry no PanDA token (swf-epicprod pull requests #5 and #6, docs/EPICPROD_PAYLOAD.md item 22). The endpoint serves only an identity with `p`, and no user had it.
- Not yet configured: the token clients. `panda_server.cfg` sets no `token_cache_config` and the default `/opt/panda/etc/panda/token_cache_config.json` does not exist, so the endpoint issues no token yet; the `rucio` and `storage` client entries and credentials come from JLab.
- Verified: before the change the endpoint refused the robot proxy with `failed: 'iddssv1' not in authorized users with 'p' in DOMA_PANDAMETA.USERS.GRIDPREF to get access token`; after the dispatcher parameters refreshed (at most 10 minutes) it answers `'token' not found for rucio`, so the permission passes and only the client configuration is missing.
- Rollback: `DELETE FROM doma_pandameta.users WHERE name = 'iddssv1';`

## 2026-10-02 to 2026-10-19: changes found on the host

Recorded 2026-10-20 from file times, backup files and the journal on the host. None was logged when made; who made each change and why are not recorded and are to be added by the editor.

- 2026-10-02: `panda_server-httpd.conf`, `SSLCertificateChainFile` from `/etc/grid-security/certificates/InCommon-RSA-IGTF-Server-CA-3.pem` to `/opt/panda/etc/certs/chain.pem` (backup `panda_server-httpd.conf-backup-2026-10-02`).
- 2026-10-07: `panda_common.cfg`, `log_level` set to `DEBUG` (the editor's copy `panda_common.cfg~` holds that version).
- 2026-10-09, with the upgrade below and not in its entry: the rollback copy `/opt/panda-backup-2026-10-09`; `argparse` 1.4.0 installed; new templates `panda_jedi.cfg.rpmnew`, `panda_server.cfg.rpmnew` and `panda_server-httpd.conf.rpmnew` written beside the live files and not reconciled; `panda_jedi.cron` rewritten.
- 2026-10-15 09:46 ET: host rebooted.
- 2026-10-18 21:32 ET: `panda_common.cfg`, `log_level` back to `INFO`; `panda_jedi` stopped 21:32 and started 21:36.
- 2026-10-19 08:54 ET: the host certificate, key and chain in `/opt/panda/etc/certs/` replaced (InCommon, valid to 2027-05-06).

## 2026-10-14:

- one-file hotfix : replaced the /opt/panda/lib/python3.11/site-packages/pandaserver/dataservice/setupper_dummy_plugin.py with the current version from github repo,
- motivation : a previous commit breaks the normal job activaition chain, causing jobs to be activated prematurally. That change was reverted in github repo. This
  single-file hotfix avoids longer process of assessing other new commits. 
- for future upgrade : just follow the usual upgrade steps to let pip upgrade the packages. 

## 2026-10-09:

- upgraded panda server to 0.7.6, commit 725129f38633613bc9729647b1c01fcb36641bc8.
- motivation
  - need the patch from Anil for token auth to JLab Rucio
  - "job generator skips tasks pinned to sites the throttler excludes" from Torre
  - other commits in between
- no update on package swf-epicprod, which stays at 0.3.0
- update to panda DB schema (to 0.1.8) required.

## 2026-10-05: ePIC job throttler, swf-epicprod 9a7aab3; wlcg MODE back to observe

- By: the ePIC production operators (Torre Wenaus with an AI session). Not logged at the time; recorded 2026-10-20 from the host and the repository.
- swf-epicprod 86d0fa9 to 9a7aab3, installed 14:53 ET (the dist-info time; `direct_url.json` names 9a7aab3). Two engine changes (swf-epicprod docs/EPIC_JOB_THROTTLER.md): 51d0831 puts the rule that held the whole work queue behind `HOLD_QUEUE_ON_SATURATED_SITE`, off, because with the wlcg mode at `throttle` it held every production pass at every site from at least 2026-09-26 while UM_GREX_PanDA_1 alone was saturated; 9a7aab3 counts a starting job as running, because jobs spend most of their life starting (median 87 of 115 min at BNL_OSG_EPIC_PROD_1, 4.9 of 5.1 at UM_GREX_PanDA_1, 2026-10-05) and counted as queued they read GREX at 0 running and always saturated.
- `DOMA_PANDA.config`: the wlcg `MODE` row set from `throttle` back to `observe` at 13:59 UTC with swf-epicprod `scripts/jedi-throttler-mode.sh`. When it had been set to `throttle` is not recorded. The wlcg row `NQUEUELIMIT_BNL_OSG_PanDA_1` 3123, present since 2026-09-17, was not logged either.
- Not recorded: a JEDI restart for the install and its verification; that day's logs have rotated. The code is in effect at the latest from the 2026-10-09 upgrade's restart, which kept swf-epicprod as installed.
- Rollback: `pip install --no-deps --force-reinstall` at 86d0fa9 and `sudo systemctl restart panda_jedi`; the MODE row with the same script.

## 2026-09-18: ePIC job throttler fix 2, swf-epicprod 86d0fa9; JEDI restarted

- By: the ePIC production operators (Torre Wenaus with an AI session), 18:30 to 18:36 ET
- swf-epicprod efcbef4 to 86d0fa9, `pip install --no-deps --force-reinstall`; `pip check` clean. Motivation: at 18:00 ET three 50,000-row tasks to NERSC_Perlmutter_epic generated in full in 30 minutes against the default limit of 2,000. The engine read each site per resource type and JEDI asks once per resource type: the SCORE pass held the site saturated from the second minute, the MCORE pass found no MCORE jobs anywhere and answered unthrottled and uncapped. A site is now one reading over every resource type, and a pass with no site at all is charged to a standing reading through the ledger, never uncapped (swf-epicprod docs/EPIC_JOB_THROTTLER.md).
- `sudo systemctl restart panda_jedi` only; no configuration or schema change.
- Verified: `panda_jedi` active, `DB schema check: OK`, 27 JediMaster processes, no tracebacks; the MCORE pass reads `NERSC_Perlmutter_epic: SATURATED queued 149994` and skips. Rollback: `--force-reinstall` at efcbef4 and the same restart.

## 2026-09-17: ePIC job throttler fix, swf-epicprod efcbef4; JEDI restarted

- By: the ePIC production operators (Torre Wenaus with an AI session), 12:15 to 12:23 ET
- swf-epicprod 9f8fbb8 to efcbef4, `pip install --no-deps --force-reinstall` (the version number, 0.3.0, did not change, so a plain install left 9f8fbb8 in place); `pip check` clean. Motivation: at 11:25 ET three 50,000-row tasks on BNL_OSG_PanDA_1 were generated in full within an hour against `NQUEUELIMIT_BNL_OSG_PanDA_1` 3123. The installed generator (master 8f155ac9) has no `excluded_sites`, so BNL_PanDA_1's room made every pass unthrottled at 300 jobs and the generator spent them on the saturated site's tasks; the share-statistics tables refresh about once a minute, so each reading was spent many times over. The engine now throttles the work queue on any saturated site when the generator cannot exclude, and keeps a grant ledger (`/var/log/panda/panda-EpicProdJobThrottler.ledger.json`, flock-shared by the generator processes) that charges each pass's cap against the reading until it changes; no uncapped pass; no lack-of-jobs parallel fill (swf-epicprod docs/EPIC_JOB_THROTTLER.md).
- `sudo systemctl restart panda_jedi` only (the throttler runs in JEDI); no configuration change, no schema change.
- Verified: `panda_jedi` active, `DB schema check: OK`, 27 JediMaster processes, no tracebacks; `engine up: exclusion_honored=False ledger=... ttl=180s` per VO in `panda-EpicProdJobThrottler.log`; first production decisions `SKIP throttled: saturated ['BNL_OSG_PanDA_1']` (queued 149,196). Rollback: `pip install --no-deps --force-reinstall` at 9f8fbb8 and the same restart.

## 2026-09-16: upgrade to master 8f155ac9; the ePIC job throttler registered

- By: the ePIC production operators (Torre Wenaus with an AI session), 16:00 to 16:12 ET; outcome note [notes/2026-09-16-panda-server-upgrade.md](../notes/2026-09-16-panda-server-upgrade.md)
- panda-server c7109f06 (1.0.0 plus 144 commits) to master 8f155ac9 (1.0.4 plus the commits through 2026-09-15; carries the `update_event_ranges` fix e3307c3d and the PostgreSQL subquery-alias fixes #790, #791); panda-common 0.1.8 to 0.1.11; installed under the production `pip freeze` as constraints, no other package moved; the stale record `panda_jedi-0.6.4.dist-info` removed before the install
- swf-epicprod 9f8fbb8 installed with `--no-deps`: the ePIC job throttler
- `panda_jedi.cfg` `[jobthrottle]`: `modConfig = wlcg:any:swf_epicprod.jedi.EpicProdJobThrottler:EpicProdJobThrottler,epic:any:swf_epicprod.jedi.EpicProdJobThrottler:EpicProdJobThrottler` (was the generic `GenJobThrottler` for both VOs). Motivation: pace job generation per queue so a task's 50,000 jobs are not activated at once (2026-09-16: three such tasks saturated the JLab Rucio catalog, and a finish had to kill 30,000 queued jobs serially). Backup `panda_jedi.cfg-backup-2026-09-16`.
- `panda_server-httpd.conf` line 82, the jedilog cache block: `Header set Content-Encoding gzip` becomes `Header set Content-Encoding gzip "expr=%{REQUEST_URI} !~ m#\.log$#"`, the maintainers' change of 2026-06-16 (b207a698): log files in the cache are served without the gzip header. Backup `panda_server-httpd.conf-backup-2026-09-16`.
- `DOMA_PANDA.config`, applied from a file with `psql`:
  `INSERT INTO doma_panda.config (app, component, vo, key, value, type, descr) VALUES ('jedi', 'epic_job_throttler', 'wlcg', 'MODE', 'observe', 'str', 'ePIC job throttler mode: observe (log only) or throttle'), ('jedi', 'epic_job_throttler', 'epic', 'MODE', 'observe', 'str', 'ePIC job throttler mode: observe (log only) or throttle');`
  Reversal: `DELETE FROM doma_panda.config WHERE component = 'epic_job_throttler';` (inert without the module in any case)
- Templates: the previous `.rpmnew` files, kept in the copy, differ from the new ones only in the httpd line above; the unit files were rewritten byte-identical (`systemctl daemon-reload` after the restart); no schema change (0.1.1)
- Verified: five services active; `DB schema check: OK` for the server and JEDI; `is_alive` 200; no tracebacks; 337 API requests in the first eight minutes all 200; running jobs (EICFast, BNL_PanDA_1) unaffected; `EpicProdJobThrottler` reported ready for `wlcg:any:any` and `epic:any:any` in `panda-JobThrottler.log` and writing readings per generation cycle in `panda-EpicProdJobThrottler.log`. Not yet exercised: an event-service job on BNL_NPPS_GPU.
- Rollback copy: `/opt/panda-backup-2026-09-16` (654 MB, proven by an empty rsync dry run and an import from its interpreter); `/opt/panda-backup-2026-09-14` and `-2026-06-07` kept

## 2026-07-23 to 2026-08-21: configuration edits

Recorded from the dated backup files on the host; the motivation is not recorded and is to be added by the editor.

- 2026-07-23: `panda_server-httpd.conf` (backup `panda_server-httpd.conf-backup-2026-07-23`)
- 2026-08-12: `panda_jedi.cfg` (backup `panda_jedi.cfg-backup-2026-08-12`)
- 2026-08-21: `panda_server.cfg` and `panda_server-httpd.conf` (backup `panda_server-httpd.conf-backup-2026-08-21`); the httpd change serves `_gz.out` files with the gzip content encoding

## 2026-06-07: coordinated upgrade of the BNL PanDA components

- By: PanDA operations at BNL
- panda-server c7109f06 (1.0.0 plus 144 commits, 2026-06-01), installed from git into a new Python 3.11 virtual environment at `/opt/panda`; panda-common 0.1.8
- The other BNL PanDA components were upgraded in the same window
- Rollback copy: `/opt/panda-backup-2026-06-07`

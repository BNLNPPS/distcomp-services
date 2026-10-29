# Perlmutter harvester: change log

Every change to the harvester `Perlmutter_test_1` and its configuration,
newest first: the date, the role that made the change, what changed with its
motivation, how it was verified, and the rollback copy.

## 2026-10-29 09:14 ET: NERSC_Perlmutter_epic_es to five workers

- By: Claude swf-1, on Torre's order (2026-10-29 ~09:13 ET, swf-1 dialog:
  "great work on getting perl to this point. go.", on five nodes).
- Changed in `panda_queueconfig.json`, queue `NERSC_Perlmutter_epic_es` only:
  `maxWorkers` 3 to 5, `nQueueLimitWorker` 3 to 5. Every other setting and
  queue unchanged.
- Why: three-node production since 15:35 ET 10/28 ran 12 of 12 jobs to
  completion without a failure, with the reconstruction-once check clean on
  each; five is Torre's maximum for Perlmutter. The front's node target
  (`front.queue.NERSC_Perlmutter_epic_es.nodes`) is set to 5 with it.
- Verified: the script's read-back shows both at 5; owner and mode unchanged
  (33294, 660). The worker count in PanDA's harvester_workers confirms the
  harvester's application of it.
- Backup: `panda_queueconfig.json-backup-20261029T131412Z`. Rollback:
  `queueconfig.py set NERSC_Perlmutter_epic_es maxWorkers=3 nQueueLimitWorker=3 --apply`.

## 2026-10-28 13:15 ET: NERSC_Perlmutter_epic_es to three workers

- By: Claude swf-1, on Torre's order (2026-10-28 12:37 ET, dialog
  01a1835f: "get us into smooth production with evgen input and 3 nodes in
  use"; 13:03 ET, 01a18377: start on 3 nodes once canary 41481 passes).
- Changed in `panda_queueconfig.json`, queue `NERSC_Perlmutter_epic_es` only:
  `maxWorkers` 1 to 3, `nQueueLimitWorker` 1 to 3, so the three workers may
  wait in Slurm together rather than one after another. Every other setting
  and queue unchanged.
- Why: Event Service production over EVGEN input on three nodes. The front's
  node target for the queue (`front.queue.NERSC_Perlmutter_epic_es.nodes`) is
  set with it; the front feed is turned on only after the canary's checks.
- Verified: the script's read-back shows both at 3; owner and mode unchanged
  (33294, 660). The harvester applies the file about ten minutes after a
  change; the worker count in PanDA's harvester_workers confirms it.
- Backup: `panda_queueconfig.json-backup-20261028T171528Z`. Rollback:
  `queueconfig.py set NERSC_Perlmutter_epic_es maxWorkers=1 nQueueLimitWorker=1 --apply`.

## 2026-10-28 09:56 ET: NERSC_Perlmutter_epic_es to one worker, task 41479 killed

- By: Claude swf-1, on Torre's order (2026-10-28: "KILL IT", "SET CEILING TO 1").
- Changed in `panda_queueconfig.json`, queue `NERSC_Perlmutter_epic_es` only:
  `maxWorkers` 4 to 1. Every other setting and queue unchanged.
- Why: between the entry below and this one, `maxWorkers` was set to 5, 3 and
  then 4 (09:43 ET, backup `panda_queueconfig.json-backup-20261028T134306Z`)
  without entries here. At 4, task 41479 ran four nodes at about 0.43 events/s
  each (units leaving the node one at a time, about 23 s apart, after
  reconstruction), its outputs named from the manifest's first row. The task
  was hard-finished the same minute.
- Verified: the script's read-back shows `maxWorkers` 1; owner and mode
  unchanged (660). The harvester applies the file about ten minutes after a
  change; the worker count in PanDA's harvester_workers confirms it.
- Backup: `panda_queueconfig.json-backup-20261028T135612Z`. Rollback:
  `queueconfig.py set NERSC_Perlmutter_epic_es maxWorkers=4 --apply`.

## 2026-10-28: NERSC_Perlmutter_epic_es back to one worker

- By: Claude swf-1, holding production to one node (Torre, 2026-10-28:
  Perlmutter stays one node).
- Changed in `panda_queueconfig.json`, queue `NERSC_Perlmutter_epic_es` only:
  `maxWorkers` 1000 to 1, `nQueueLimitWorker` 100 to 1, the rollback of the
  change below. Every other setting and queue unchanged.
- Why: the queue's first Event Service task over EVGEN input (41479,
  swf-epicprod NERSC_PERLMUTTER.md, EVGEN input in production) made one job
  per input file at once, nine activated at 09:15 ET, and in pull mode the
  harvester submits a worker, a whole node, for each activated job. The
  production system's one-task rule held one task, not one job. With one
  worker the jobs run one after another. A test beside production needs the
  limit raised again for its run.
- Verified: the script's read-back shows both values; owner and mode
  unchanged (660).
- Backup: `panda_queueconfig.json-backup-20261028T131649Z`. Rollback:
  `queueconfig.py set NERSC_Perlmutter_epic_es maxWorkers=1000 nQueueLimitWorker=100 --apply`.

## 2026-10-27: NERSC_Perlmutter_epic_es worker limits no longer bind

- By: Claude swf-1, on Torre's word that the production system manages
  Perlmutter usage and the harvester does not limit it.
- Changed in `panda_queueconfig.json`, queue `NERSC_Perlmutter_epic_es` only:
  `maxWorkers` 1 to 1000, `nQueueLimitWorker` 1 to 100. Two lines; every other
  setting and queue unchanged.
- Why: the harvester held the queue at one worker. With production's job
  running it reported one worker running and none to submit while test task
  41431 (job 6250592) and a one-core test job waited activated, so no test could
  run beside production. Production stays at one node through its feeder
  (swf-epicprod `perlmutter_production`, which counts only its own samples);
  in pull mode the harvester submits no more workers than activated jobs.
  `nQueueLimitWorker` stays above zero, where the pull-mode computation needs a
  value.
- How: [queueconfig.py](queueconfig.py) through the IRI API. The final copy over
  the live file reported "preserving times ... Operation not permitted"; the
  content was written, the file kept its owner and mode 660, and the side file
  was then removed by hand. The script now treats that failure as expected.
- Verified: the live file equals the backup with exactly the two settings
  changed.
- Backup: `panda_queueconfig.json-backup-20261027T160416Z`. Rollback:
  `queueconfig.py set NERSC_Perlmutter_epic_es maxWorkers=1 nQueueLimitWorker=1 --apply`.

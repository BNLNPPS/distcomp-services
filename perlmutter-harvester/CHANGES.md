# Perlmutter harvester: change log

Every change to the harvester `Perlmutter_test_1` and its configuration,
newest first: the date, the role that made the change, what changed with its
motivation, how it was verified, and the rollback copy.

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

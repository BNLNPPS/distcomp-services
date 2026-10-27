# Perlmutter harvester

The harvester `Perlmutter_test_1` serves the ePIC queues at NERSC Perlmutter
(`NERSC_Perlmutter_epic`, `NERSC_Perlmutter_epic_es` and the test and GPU
queues). It runs on a Perlmutter login node from the installation
`/global/common/software/m3763/panda-harvester`, under the account that
operates it, and submits Slurm jobs in the `m3763` allocation. Its queue
configuration is `etc/panda/panda_queueconfig.json` there, with the Slurm
templates and wrappers beside it. Changes are logged in [CHANGES.md](CHANGES.md).

## Access

The installation's configuration directory and its files belong to the group
`m3763` with group read and write. Any `m3763` member reaches them through the
NERSC IRI API (`https://api.iri.nersc.gov`, filesystem endpoints on the
resource `common`) with that member's IRI token. On `pandaserver02` the token
of an `m3763` member is refreshed daily into
`/data/wguan2/hpc_tokens/nersc_iri_config.yaml`; scripts read it from that file
each use and never print it.

The harvester reports to the PanDA server, where its state can be read without
NERSC access: per-queue worker counts (`harvester_worker_stats`, including the
workers it intends to submit, `to_submit`), its messages (`harvester_dialogs`),
its metrics and its API calls (`panda-api_harvester.log` on `pandaserver01`).

## Queue settings

[queueconfig.py](queueconfig.py) reads a queue's settings and changes them:

```
queueconfig.py show NERSC_Perlmutter_epic_es
queueconfig.py set NERSC_Perlmutter_epic_es maxWorkers=1000 --apply
```

A change edits only the named settings in place (the file mixes tabs and
spaces and is not re-serialized), keeps a dated backup
`panda_queueconfig.json-backup-<UTC stamp>` beside the file, uploads the edit
to a side file and copies it over the live file in place, so the live file
keeps its owner and mode, and reads it back against the edit. The API's copy
also tries to carry the timestamps, which only the owner may set; that failure
is expected and the read-back decides. The harvester rereads the file within
minutes (its `qconf` check interval).

The production system, not the harvester, decides how much runs: the
production feeder adds work, and the queue registry closes a queue at its
allocation floor. In pull mode the harvester starts no more workers than there
are activated jobs (`worker_adjuster.py`), so `maxWorkers` and
`nQueueLimitWorker` are set high enough never to bind.

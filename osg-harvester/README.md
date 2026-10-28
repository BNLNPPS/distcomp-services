# OSG harvester (osgsub01)

`osgsub01.sdcc.bnl.gov` runs the harvester instance `BNL_osg_harvester_1`,
which submits ePIC's OSG pilots (`BNL_OSG_PanDA_1`; `BNL_OSG_EPIC_PROD_1`
retired) to the OSG pools through a local HTCondor schedd. The submission
path, templates and pool are described in swf-epicprod
[docs/OSG_SUBMISSION.md](https://github.com/BNLNPPS/swf-epicprod/blob/main/docs/OSG_SUBMISSION.md).
Changes are logged in [CHANGES.md](CHANGES.md).

## Pilot-log retention

Harvester writes each pilot's stdout (`.out`), stderr (`.err`) and condor
user log (`.log`) under `/var/data/atlpan/condor_logs`, one directory per
submission hour (`YY-MM-DD_HH`), served at the queues' `logBaseURL`,
`https://osgsub01.sdcc.bnl.gov/condor_logs/`. Neither harvester nor the host
rotates them. On 28 October 2026 they held 437 GB of the 520 GB `/var`, which
also holds harvester's database and the condor spool; a full `/var` stops OSG
submission.

[`pilot-log-retention.py`](pilot-log-retention.py) runs hourly as `atlpan`
(cron `/etc/cron.d/epicprod-pilot-log-retention`, minute 17, lowest CPU and
I/O priority) and:

- gzips the `.out`, `.err` and `.log` files of an hour directory once they
  have not changed for 6 hours, unless a job in the condor queue names them;
- removes an hour directory whose newest file is older than 6 days, unless a
  job in the queue names a file in it.

Six days covers every use of a pilot log: diagnosis of a recent pilot or
worker failure. The job's own record stays in PanDA and its payload logs in
the job's log tarball in Rucio. A compressed log is served as `NAME.gz`, so a
link to `NAME` no longer resolves; a removed log is gone. Named directories
(trial and cohort evidence such as `native-image-dispatch-20261023`) are
never touched. A failed queue listing stops the run before anything changes.

Each run appends one JSON line to
`/var/data/atlpan/harvester_common/pilot-log-retention/retention.log`:
files compressed and their size before, directories removed and their size,
directories kept for queued jobs, failures and the free space on `/var`.

Install or update from swf-testbed, after committing:

```bash
cd distcomp-services/osg-harvester && ./install-pilot-log-retention.sh
```

The installer copies the script and its `COMMIT` to the host, runs it once
with `--dry-run` as `atlpan`, and writes the cron entry.
`./install-pilot-log-retention.sh --remove` removes the cron entry. A manual
run: `sudo -u atlpan /usr/bin/python3
/var/data/atlpan/harvester_common/pilot-log-retention/pilot-log-retention.py
[--dry-run] [--compress-hours H] [--delete-days D]`. `gunzip` restores a
compressed log.

The host's `disk_space_monitor.sh` (atlpan cron, mails the PanDA service
maintainer when a filesystem passes 85%) fails on every run while `df`
errors on a dead CVMFS mount (`/cvmfs/cvmfs-config.cern.ch`, 28 October
2026), so it is not an alert at present.

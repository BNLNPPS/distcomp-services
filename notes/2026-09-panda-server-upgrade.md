# PanDA server upgrade, September 2026

The specifics of this upgrade of the PanDA server on `pandaserver01.sdcc.bnl.gov`, planned under the standing procedure in [panda-server/UPGRADE.md](../panda-server/UPGRADE.md). Pending execution; the outcome is appended here and logged in [panda-server/CHANGES.md](../panda-server/CHANGES.md).

## Motivation

- `update_event_ranges` in `api/v1/event_api.py` returns 500 on every call in the installed code: the response is built as a set and cannot be serialized, after the ranges have been updated in the database. The pilot cannot complete an event-service job against it. Fixed on master 2026-09-11 (e3307c3d). The event service on Perlmutter and on the GPU test queue depends on the fix.
- The ePIC job throttler is registered in JEDI at the same restart, in observe mode: it logs its readings and answers as the current throttler does.
- The installed commit dates from 2026-06-01; the delta carries the fixes of releases 1.0.1, 1.0.2 and 1.0.4.

## Installed and target

| | Installed | Target |
|---|---|---|
| panda-server | 1.0.0 plus 144 commits, c7109f06 (2026-06-01), installed 2026-06-07 | master at a commit at or after e3307c3d. At writing the head is 09c8b553 (2026-09-14), 486 commits past the installed one. Release 1.0.4 (2026-09-07) predates the fix; a release tagged before execution that carries it becomes the target. |
| panda-common | 0.1.8 | 0.1.11, the pin at master, resolved from PyPI |
| Minimum database schema | 0.1.1 | 0.1.1. No database change. The database passed the check at the 2026-09-15 restart. |
| Python | 3.11.6; 3.10 or later required | unchanged |
| Templates | | one line in `panda_server-httpd.conf` (below) |
| Entry points | | none removed from the legacy dispatcher; the `api/v1` changes are type annotations, the event fix, and a parameter rename in the task API's asynchronous requests (`async_id`) |

The target is a state of master rather than a release: no release carries the fix, the next release has no date, and the upgrade is done in the present lull between campaigns rather than deferred. The commits past 1.0.4 are, at writing, the maintainers' type-annotation sweep, the workflows4 branch and the event fixes. The canary task and the tree copy bound the exposure.

Two open pull requests on panda-server fix unaliased subqueries for PostgreSQL, the backend here (#790, #791). The target commit is chosen at execution to include what has been merged by then.

## Integrity gate result

Run 2026-09-15 on `pandaserver02` against 09c8b553 under production's package versions: the constraint solve moved panda-server and panda-common only, `pip check` clean; 298 modules imported, the four failures being two test modules and the Kafka publisher and processor, which need `confluent_kafka`, not installed on production and not configured; all 42 configured targets loaded (the 20 `modConfig` entries, 16 daemon modules, 5 plugins, the ePIC throttler); `update_event_ranges` builds its response as a dict.

## Configuration changes

1. `panda_server-httpd.conf`: in the cache directory block, `Header set Content-Encoding gzip` becomes `Header set Content-Encoding gzip "expr=%{REQUEST_URI} !~ m#\.log$#"`, the maintainers' change of 2026-06-16 (b207a698): log files in the cache are served without the gzip header. The block added locally on 2026-08-21 for `_gz.out` files is unchanged.
2. `panda_jedi.cfg`, section `[jobthrottle]`: the epic entry of `modConfig` becomes `epic:any:swf_epicprod.jedi.EpicProdJobThrottler:EpicProdJobThrottler`.
3. `DOMA_PANDA.config`: component `epic_job_throttler`, app `jedi`, VO `epic`, key `MODE`, value `observe`. Per-site limits are added later from the observed readings.
4. The swf-epicprod package installed in the virtual environment at a pinned commit, `pip install "git+https://github.com/BNLNPPS/swf-epicprod.git@<commit>"`; it declares no dependencies, and the throttler module imports only `pandacommon` and `pandajedi`.
5. The record `panda_jedi-0.6.4.dist-info` is removed from `site-packages` before the install. It describes a package whose files panda-server overwrote in June (the files on disk match the panda-server record, not this one); left in place, a `pip uninstall panda-jedi` would delete live JEDI files.

## Verification specific to this upgrade

- An event-service job on the BNL_NPPS_GPU test queue completes its ranges; the probe of 2026-09-09 saw the 500 on every update.
- `panda-EpicProdJobThrottler.log` carries a reading per generation cycle, and JEDI generates jobs as before.
- A canary task on a production queue finishes; harvester workers keep appearing and jobs dispatch.

## Rollback

A copy of the tree made 2026-09-14 exists (`/opt/panda-backup-2026-09-14`, identical to the live tree as of 2026-09-15); a fresh copy is taken at execution regardless. The throttler registration is in the `panda_jedi.cfg` of the copy; the configuration rows are inert without the module.

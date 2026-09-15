# PanDA server upgrade at BNL

This document is the procedure for upgrading the PanDA server and JEDI on the ePIC PanDA server host at BNL, the plan for the pending upgrade, and the pointer to the record of upgrades done. The procedure is standing. The pending-upgrade section is written for each upgrade, circulated to PanDA operations at BNL and the panda-server maintainers for comment, and logged in [CHANGES.md](CHANGES.md) when the upgrade is executed.

## The installation

| | |
|---|---|
| Host | `pandaserver01.sdcc.bnl.gov`, RHEL 8.9 |
| Tree | `/opt/panda`, a Python 3.11 virtual environment. panda-server is installed by pip from the git repository; the installed commit is recorded in the package's `direct_url.json`. panda-common comes from PyPI as its dependency. |
| Packages | panda-server (JEDI is part of it, as `pandajedi`), panda-common, panda-client-light, panda-cacheschedconfig, the idds client libraries, rucio-clients |
| Services | systemd units run as `atlpan`: `panda` (the database schema check at start), `panda_httpd` (Apache with mod_wsgi, ports 25080 and 25443), `panda_daemon`, `panda_jedi`, `panda_mcp` (port 25888) |
| Configuration | `/opt/panda/etc/panda`: `panda_server.cfg`, `panda_jedi.cfg`, `panda_common.cfg`, `panda_server-httpd.conf` and the JSON files, linked from `/etc/panda`; the service environment in `/etc/sysconfig/panda_server_env` and `panda_jedi_env`. The live files are maintained by hand and carry the site's settings; the templates a package ships land beside them as `.rpmnew` files. |
| Database | `pandadb01.sdcc.bnl.gov`, PostgreSQL, schemas `DOMA_PANDA`, `DOMA_PANDAMETA`, `DOMA_PANDAARCH`. The schema version in `pandadb_version` is checked against the code's minimum at each start of `panda` and `panda_jedi`. |
| Logs | `/var/log/panda`. Nightly rotation at about 03:15 ET stops and restarts the services. |
| Clients | harvester (`pandaharvester01`), the pilot and iDDS use the server's HTTP API. |

The maintainers' installation guide: [PanDA server](https://panda-wms.readthedocs.io/en/latest/installation/server.html), [database administration](https://panda-wms.readthedocs.io/en/latest/database/administration.html).

## Procedure

1. **Assessment.** Record the installed commit (`pip show panda-server`, `direct_url.json`) and choose the target: a release tag, or a master commit when a needed fix is not yet released. Read the delta for the four things that decide the shape of an upgrade: the minimum database schema version (`pandaserver/taskbuffer/PandaDBSchemaInfo.py`, checked by the server's and JEDI's `SchemaChecker.py`), the dependency pins (`pyproject.toml`, panda-common first), the configuration and service templates (`templates/`), and the entry points harvester, the pilot and iDDS call (`pandaserver/api/v1`, the legacy dispatcher). A schema change means the database patch from the panda-database repository before the code. Write the pending-upgrade section from the reading and circulate it.

2. **Timing and notice.** A lull in production, between campaigns where possible. The restart interrupts the server for about a minute; harvester and the pilot retry their calls, and the nightly rotation restart shows the services tolerate it. Notice to the production operations list before and after.

3. **Preservation.** `cp -a /opt/panda /opt/panda-backup-<date>` (about 650 MB; the root filesystem must have the room) and `pip freeze > /opt/panda-backup-<date>/pip-freeze.txt`. The copy holds the code, the live configuration and the previous templates, and is the rollback.

4. **Installation.** In the virtual environment, `pip install "git+https://github.com/PanDAWMS/panda-server.git@<tag or commit>"`, which brings panda-common at the pinned version; no other package is upgraded. Confirm with `pip show panda-server` and `pip check`.

5. **Configuration.** The install writes the new templates as `.rpmnew` files beside the live ones. Diff each new `.rpmnew` against the previous one (kept in the copy) to see what the maintainers changed, apply the changes that apply here to the live file, and record each with its motivation in the pending-upgrade section. A live file is never replaced by a template.

6. **Restart.** `systemctl restart panda panda_httpd panda_daemon panda_jedi panda_mcp`. The journal must show `DB schema check: OK` for the server and for JEDI.

7. **Verification.** The services are active; `http://pandaserver01.sdcc.bnl.gov:25080/api/v1/system/is_alive` returns 200; `/var/log/panda/panda_*_stderr.log` and the JEDI log carry no traceback after a few cycles; harvester workers keep appearing and jobs keep dispatching, read from the production monitor; a canary task on a production queue runs to completion; the fix that motivated the upgrade is exercised; the ePIC modules registered in JEDI report in their logs. An hour of watching.

8. **Rollback.** Stop the services, set the failed tree aside, restore the copy, start: `mv /opt/panda /opt/panda-failed-<date>; cp -a /opt/panda-backup-<date> /opt/panda`. Minutes. The copy carries the configuration as it was.

9. **Record.** Log the upgrade in [CHANGES.md](CHANGES.md): the date, the versions, the configuration changes with their motivation, the verification, the rollback copy and any deviation from the plan. Clear the pending-upgrade section.

## ePIC modules in JEDI

JEDI plugins owned by ePIC production are registered in `panda_jedi.cfg` `modConfig` lines and installed in the virtual environment from the [swf-epicprod](https://github.com/BNLNPPS/swf-epicprod) repository at a pinned commit. Each upgrade re-verifies them: `panda_jedi` starts without an import error in the JEDI log, and each module writes its own log. Registered after the pending upgrade: the [ePIC job throttler](https://github.com/BNLNPPS/swf-epicprod/blob/main/docs/EPIC_JOB_THROTTLER.md).

Changes to panda-server itself go to the maintainers as pull requests. The server runs the maintainers' releases or master commits, never a local patch.

## Pending upgrade: September 2026

### Motivation

- `update_event_ranges` in `api/v1/event_api.py` returns 500 on every call in the installed code: the response is built as a set and cannot be serialized, after the ranges have been updated in the database. The pilot cannot complete an event-service job against it. Fixed on master 2026-09-11 (e3307c3d). The event service on Perlmutter and on the GPU test queue depends on the fix.
- The ePIC job throttler is registered in JEDI at the same restart, in observe mode: it logs its readings and answers as the current throttler does.
- The installed commit dates from 2026-06-01; the delta carries the fixes of releases 1.0.1, 1.0.2 and 1.0.4.

### Installed and target

| | Installed | Target |
|---|---|---|
| panda-server | 1.0.0 plus 144 commits, c7109f06 (2026-06-01), installed 2026-06-07 | master at a commit at or after e3307c3d. At writing the head is 09c8b553 (2026-09-14), 486 commits past the installed one. Release 1.0.4 (2026-09-07) predates the fix; a release tagged before execution that carries it becomes the target. |
| panda-common | 0.1.8 | 0.1.11, the pin at master, resolved from PyPI |
| Minimum database schema | 0.1.1 | 0.1.1. No database change. The database passed the check at the 2026-09-15 restart. |
| Python | 3.11.6; 3.10 or later required | unchanged |
| Templates | | one line in `panda_server-httpd.conf` (below) |
| Entry points | | none removed from the legacy dispatcher; the `api/v1` changes are type annotations, the event fix, and a parameter rename in the task API's asynchronous requests (`async_id`) |

Two open pull requests on panda-server fix unaliased subqueries for PostgreSQL, the backend here (#790, #791). The target commit is chosen at execution to include what has been merged by then.

### Configuration changes

1. `panda_server-httpd.conf`: in the cache directory block, `Header set Content-Encoding gzip` becomes `Header set Content-Encoding gzip "expr=%{REQUEST_URI} !~ m#\.log$#"`, the maintainers' change of 2026-06-16 (b207a698): log files in the cache are served without the gzip header. The block added locally on 2026-08-21 for `_gz.out` files is unchanged.
2. `panda_jedi.cfg`, section `[jobthrottle]`: the epic entry of `modConfig` becomes `epic:any:swf_epicprod.jedi.EpicProdJobThrottler:EpicProdJobThrottler`.
3. `DOMA_PANDA.config`: component `epic_job_throttler`, app `jedi`, VO `epic`, key `MODE`, value `observe`. Per-site limits are added later from the observed readings.
4. The swf-epicprod package installed in the virtual environment at a pinned commit, `pip install "git+https://github.com/BNLNPPS/swf-epicprod.git@<commit>"`; it declares no dependencies, and the throttler module imports only `pandacommon` and `pandajedi`.
5. The record `panda_jedi-0.6.4.dist-info` is removed from `site-packages` before the install. It describes a package whose files panda-server overwrote in June (the files on disk match the panda-server record, not this one); left in place, a `pip uninstall panda-jedi` would delete live JEDI files.

### Verification specific to this upgrade

- An event-service job on the BNL_NPPS_GPU test queue completes its ranges; the probe of 2026-09-09 saw the 500 on every update.
- `panda-EpicProdJobThrottler.log` carries a reading per generation cycle, and JEDI generates jobs as before.
- A canary task on a production queue finishes; harvester workers keep appearing and jobs dispatch.

### Rollback

A copy of the tree made 2026-09-14 exists (`/opt/panda-backup-2026-09-14`, identical to the live tree as of 2026-09-15); a fresh copy is taken at execution regardless. The throttler registration is in the `panda_jedi.cfg` of the copy; the configuration rows are inert without the module.

## Record

Executed upgrades are logged in [CHANGES.md](CHANGES.md).

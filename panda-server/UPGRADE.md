# PanDA server upgrade at BNL

This document is the standing procedure for upgrading the PanDA server and JEDI on the ePIC PanDA server host at BNL. Each upgrade has a note under `notes/` with its specifics, written from the assessment, circulated to PanDA operations at BNL and the panda-server maintainers for comment, completed at execution, and logged in [CHANGES.md](CHANGES.md).

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

1. **Assessment.** Record the installed commit (`pip show panda-server`, `direct_url.json`) and choose the target: a release tag, or a master commit when a needed fix is not yet released. Read the delta for the four things that decide the shape of an upgrade: the minimum database schema version (`pandaserver/taskbuffer/PandaDBSchemaInfo.py`, checked by the server's and JEDI's `SchemaChecker.py`), the dependency pins (`pyproject.toml`, panda-common first), the configuration and service templates (`templates/`), and the entry points harvester, the pilot and iDDS call (`pandaserver/api/v1`, the legacy dispatcher). A schema change means the database patch from the panda-database repository before the code. Write the upgrade's note under `notes/` from the reading and circulate it.

2. **Integrity gate.** Before the target touches the host, it is installed on another host into a throwaway virtual environment of the same Python, with the production `pip freeze` as pip constraints, so that the result is the package set the real install produces: `pip check` must pass and the constraint solve must move no package but panda-server and panda-common. In that environment, with the production settings that shape imports (the database backend, the schema names, the log directory), [`gate/import_walk.py`](gate/import_walk.py) imports every module of `pandaserver`, `pandajedi` and `pandacommon`, and [`gate/config_load.py`](gate/config_load.py) imports every class and module the production configuration names: the `modConfig` targets of `panda_jedi.cfg`, the enabled daemons of `panda_server.cfg`, the adder, setupper and closer plugins, and the ePIC modules. A failure outside test modules and unconfigured optional integrations stops the upgrade at that commit. The fix that motivates the upgrade is confirmed present in the installed code. [`gate/run-gate.sh`](gate/run-gate.sh) runs the gate; its inputs are the production `pip freeze` and the two configuration files without their password lines. The gate does not reach SQL that is wrong only at run time on this backend; the verification step and the rollback copy cover that.

3. **Timing and notice.** A lull in production, between campaigns where possible. The restart interrupts the server for about a minute; harvester and the pilot retry their calls, and the nightly rotation restart shows the services tolerate it. Notice to the production operations list before and after.

4. **Preservation.** `cp -a /opt/panda /opt/panda-backup-<date>` (about 650 MB; the root filesystem must have the room) and `pip freeze > /opt/panda-backup-<date>/pip-freeze.txt`. The copy holds the code, the live configuration and the previous templates, and is the rollback.

5. **Installation.** In the virtual environment, `pip install "git+https://github.com/PanDAWMS/panda-server.git@<tag or commit>"`, which brings panda-common at the pinned version; no other package is upgraded. Confirm with `pip show panda-server` and `pip check`.

6. **Configuration.** The install writes the new templates as `.rpmnew` files beside the live ones. Diff each new `.rpmnew` against the previous one (kept in the copy) to see what the maintainers changed, apply the changes that apply here to the live file, and record each with its motivation in the upgrade's note. A live file is never replaced by a template.

7. **Restart.** `systemctl restart panda panda_httpd panda_daemon panda_jedi panda_mcp`. The journal must show `DB schema check: OK` for the server and for JEDI.

8. **Verification.** The services are active; `http://pandaserver01.sdcc.bnl.gov:25080/api/v1/system/is_alive` returns 200; `/var/log/panda/panda_*_stderr.log` and the JEDI log carry no traceback after a few cycles; harvester workers keep appearing and jobs keep dispatching, read from the production monitor; a canary task on a production queue runs to completion; the fix that motivated the upgrade is exercised; the ePIC modules registered in JEDI report in their logs. An hour of watching.

9. **Rollback.** Stop the services, set the failed tree aside, restore the copy, start: `mv /opt/panda /opt/panda-failed-<date>; cp -a /opt/panda-backup-<date> /opt/panda`. Minutes. The copy carries the configuration as it was.

10. **Record.** Log the upgrade in [CHANGES.md](CHANGES.md): the date, the versions, the configuration changes with their motivation, the verification, the rollback copy and any deviation from the plan; complete the upgrade's note with the outcome.

## ePIC modules in JEDI

JEDI plugins owned by ePIC production are registered in `panda_jedi.cfg` `modConfig` lines and installed in the virtual environment from the [swf-epicprod](https://github.com/BNLNPPS/swf-epicprod) repository at a pinned commit. Each upgrade re-verifies them: `panda_jedi` starts without an import error in the JEDI log, and each module writes its own log. Registered after the pending upgrade: the [ePIC job throttler](https://github.com/BNLNPPS/swf-epicprod/blob/main/docs/EPIC_JOB_THROTTLER.md).

Changes to panda-server itself go to the maintainers as pull requests. The server runs the maintainers' releases or master commits, never a local patch.

## Pending upgrade

The current upgrade's specifics are the note [notes/2026-09-panda-server-upgrade.md](../notes/2026-09-panda-server-upgrade.md). Each upgrade has one note under `notes/`, written at planning and completed at execution.

## Record

Executed upgrades are logged in [CHANGES.md](CHANGES.md).

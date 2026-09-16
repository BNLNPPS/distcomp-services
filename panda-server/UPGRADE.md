# PanDA server upgrade at BNL

This document is the procedure for upgrading the PanDA server and JEDI on the ePIC PanDA server host at BNL, and the pointer to the record of upgrades done. The procedure is standing and is written to be executed step by step, each step with its command, its expected output and its check; an operator or an AI session runs it as written and stops at the first check that fails. The specifics of a pending upgrade (target, delta, configuration changes) are written into the Pending upgrade section, circulated to PanDA operations at BNL and the panda-server maintainers for comment, and moved into [CHANGES.md](CHANGES.md) when the upgrade is executed.

## The installation

| | |
|---|---|
| Host | `pandaserver01.sdcc.bnl.gov`, RHEL 8.9. Reached from `pandaserver02` (swf-testbed) through the SCDF gateway: `ssh -A -o BatchMode=yes wenauseic@ssh.sdcc.bnl.gov "ssh -o BatchMode=yes pandaserver01 '<command>'"`. The account has passwordless `sudo`. |
| Tree | `/opt/panda`, root-owned, a Python 3.11 virtual environment (`/opt/panda/bin/python`, `/opt/panda/bin/pip`). panda-server is installed by pip from the git repository; the installed commit is in `/opt/panda/lib/python3.11/site-packages/panda_server-*.dist-info/direct_url.json`. panda-common comes from PyPI as its dependency. |
| Packages | panda-server (JEDI is part of it, as `pandajedi`, since 2025-08-28; the separate panda-jedi package the official JEDI guide still names is archived), panda-common, panda-client-light, panda-cacheschedconfig, the idds client libraries, rucio-clients, and the ePIC modules from swf-epicprod (below) |
| Services | systemd units run as `atlpan`: `panda` (the database schema check at start), `panda_httpd` (Apache with mod_wsgi, ports 25080 and 25443), `panda_daemon`, `panda_jedi` (`Type=forking`, `RemainAfterExit=true`: `systemctl status` reads `active (exited)` while its `JediMaster.py` processes run), `panda_mcp` (port 25888). The unit files live in `/opt/panda/etc/panda/systemd/` and are linked from `/etc/systemd/system/`; a pip install rewrites them, so systemd reports them changed on disk after every install even when their content is identical. |
| Configuration | `/opt/panda/etc/panda`: `panda_server.cfg`, `panda_jedi.cfg`, `panda_common.cfg`, `panda_server-httpd.conf` and the JSON files, linked from `/etc/panda`; the service environment in `/etc/sysconfig/panda_server_env` and `panda_jedi_env`. The live files are maintained by hand and carry the site's settings; the templates a package ships land beside them as `.rpmnew` files, overwriting the previous `.rpmnew` files, which is why the copy of step 4 is the only place the previous templates survive. Dated backups of edited files are kept beside them, `<file>-backup-<date>`. |
| Database | `pandadb01.sdcc.bnl.gov`, PostgreSQL, database `panda_db`, user `panda` (password `dbpasswd` in `/etc/panda/panda_server.cfg`, readable with `sudo`), schemas `DOMA_PANDA`, `DOMA_PANDAMETA`, `DOMA_PANDAARCH` (lower case in psql). The schema version in `pandadb_version` is checked against the code's minimum at each start of `panda` and `panda_jedi`. `psql` is installed on the host. |
| Logs | `/var/log/panda`, owned by `atlpan`, mode 666 on the per-component `panda-<Component>.log` files. Timestamps in the JEDI and access logs are UTC. Nightly rotation at about 03:15 ET stops and restarts the services. |
| Clients | harvester (`pandaharvester01`, `pandaharvester02`), the OSG submit host (`osgsub01`), iDDS (`idds01`), the CERN monitor (`aipanda105`) and the pilot use the server's HTTP API. |

The maintainers' guides: [PanDA server](https://panda-wms.readthedocs.io/en/latest/installation/server.html), [JEDI](https://panda-wms.readthedocs.io/en/latest/installation/jedi.html), [database administration](https://panda-wms.readthedocs.io/en/latest/database/administration.html). They describe installation, not upgrades; everything they say that bears on an upgrade is in this procedure: the install from git, the `.rpmnew` templates beside the live files, the units and logrotate files linked from the tree, and the schema check at start (the services exit with "This version of PanDA Server/JEDI requires DB schema version X.Y.Z ..." when the database is below the code's minimum; patches come from the panda-database repository).

## Rules

1. **Edit files on the host by script, never by an inline `sed` or SQL string through the two-hop ssh.** The two shells' quoting mangled an httpd expression and a SQL statement on 2026-09-16. Write the edit as a small Python script or a `.sql` file, ship it with `tar ... | ssh ... 'tar -x'` into `/tmp/upgrade-<date>/`, run it there, and print the changed line back.
2. **Never run the server's code on the host as your own user.** A test import of a JEDI plugin creates its `panda-<Component>.log` under your user; `atlpan` then cannot write it. Prove imports in the gate environment, not on the host; if a host-side import is unavoidable, `chown atlpan:atlpan` and `chmod 666` the log file it created before the restart.
3. **A live configuration file is never replaced by a template.** Templates are diffed; changes are applied by hand to the live file.
4. **Every check has an expected output written here. A check that does not read as written stops the procedure**; the rollback rule (Reversibility) says when to roll back rather than diagnose.
5. **Read timestamps as UTC** in the JEDI and access logs; the journal is in local time (ET).

## Procedure

### 1. Assessment

Record the installed commit and choose the target. Read the delta for the four things that decide the shape of the upgrade, and write the Pending upgrade section from the reading; circulate it.

```
# on the host
/opt/panda/bin/pip show panda-server panda-common | grep -E "^(Name|Version)"
cat /opt/panda/lib/python3.11/site-packages/panda_server-*.dist-info/direct_url.json
# in a panda-server checkout
git fetch origin; git log --oneline origin/master -3; git tag --sort=-creatordate | head -1
git diff <installed>..<target> -- pandaserver/taskbuffer/PandaDBSchemaInfo.py     # schema minimum
git diff <installed>..<target> -- pyproject.toml | grep "^[-+]" | grep -i "panda-common\|>="   # pins
git diff --stat <installed>..<target> -- templates/                                # config, units, logrotate, sysconfig
git diff --stat <installed>..<target> -- pandaserver/api/v1 pandaserver/server     # entry points
```

- A raised schema minimum means the database patch from panda-database before the code, and a different rollback (Reversibility).
- A changed unit or logrotate template means `systemctl daemon-reload` before the restart in step 7.
- The target is a release tag, or a master commit when a needed fix is not yet released; the commit is chosen at execution to include what has merged by then, and the gate is re-run on it.

### 2. Integrity gate

On `pandaserver02`, with the production `pip freeze` as constraints, install the target into a throwaway venv and import everything the production configuration names. Inputs: the production freeze without its panda-server, panda-common and panda-jedi lines; the two configuration files without their password lines; a checkout of swf-epicprod at the commit to be pinned.

```
cd /data/wenauseic/panda-gate
GATE_DIR=$PWD/gate-<target> PYTHONPATH_EXTRA=/data/wenauseic/github/swf-epicprod \
  bash /data/wenauseic/github/distcomp-services/panda-server/gate/run-gate.sh <target> \
  constraints-prod.txt epic_jedi.cfg epic_server.cfg swf_epicprod.jedi.EpicProdJobThrottler:EpicProdJobThrottler
```

`run-gate.sh` stops after the import walk when any module fails (`set -o pipefail`); run `config_load.py` by hand then:

```
W=/data/wenauseic/panda-gate/gate-<target>; SP=$W/venv/lib/python3.11/site-packages
cd $W && PANDA_HOME=$W/venv TZ=UTC PYTHONPATH=$SP/pandacommon:$SP/pandaserver:/data/wenauseic/github/swf-epicprod \
  $W/venv/bin/python /data/wenauseic/github/distcomp-services/panda-server/gate/config_load.py \
  /data/wenauseic/panda-gate/epic_jedi.cfg /data/wenauseic/panda-gate/epic_server.cfg \
  swf_epicprod.jedi.EpicProdJobThrottler:EpicProdJobThrottler | tee $W/config-load.log | tail -3
```

Expected: `pip check` prints `No broken requirements found`; the import walk reports failures only in test modules (`pandaserver.workflow.pcwl_test`, `pandacommon.test.logtest`) and the Kafka publisher and processor (`confluent_kafka`, not installed and not configured); `config_load.py` prints `<N> targets, 0 failed` (42 on 2026-09-16). Confirm the motivating fix in the gate venv's installed code (`grep` for it). Anything else stops the upgrade at that commit.

### 3. Timing and notice

A lull in production: read the non-terminal tasks and the live job table before starting (from the monitor: `panda_get_activity`, or on the database `jedi_tasks` by status and `jobsactive4` by site and status). Running jobs ride through the restart (harvester and the pilot retry). Notice to the production operations list before and after; a note to any user with jobs running.

### 4. Preservation

```
D=/opt/panda-backup-<date>
test -e $D && echo EXISTS && exit
sudo cp -a /opt/panda $D
sudo /opt/panda/bin/pip freeze > /tmp/pip-freeze-<date>.txt && sudo cp /tmp/pip-freeze-<date>.txt $D/pip-freeze.txt
sudo rsync -a --dry-run --itemize-changes /opt/panda/ $D/
$D/bin/python -c "import pandaserver, pandajedi, pandacommon; print(pandaserver.__file__)"
du -sh $D; df -h /
```

Expected: the rsync dry run prints one line, `.d..t...... ./` (the top directory's mtime, from the freeze file written into the copy), and nothing else; the import prints a path under the copy; about 654 MB; root keeps at least two tree sizes free (a rollback holds the failed tree beside the copy). Older copies stay until the upgrade is logged as verified.

### 5. Installation

Under the production freeze as constraints, so that nothing but panda-server and panda-common can move (what the gate proved). Remove first any package record that describes files panda-server owns (the `panda_jedi-0.6.4.dist-info` case of 2026-09-16: a `pip uninstall` of it would have deleted live JEDI files).

```
SP=/opt/panda/lib/python3.11/site-packages
ls -d $SP/panda_jedi-* 2>/dev/null && sudo rm -rf $SP/panda_jedi-*.dist-info
grep -v -i "^panda-server\|^panda-common\|^panda-jedi" /opt/panda-backup-<date>/pip-freeze.txt > /tmp/constraints-prod.txt
sudo /opt/panda/bin/pip install -c /tmp/constraints-prod.txt \
  "panda-server[postgres,mcp] @ git+https://github.com/PanDAWMS/panda-server.git@<target>" > /tmp/pip-install-panda-server.log 2>&1
sudo /opt/panda/bin/pip check
/opt/panda/bin/pip show panda-server panda-common | grep -E "^(Name|Version)"
cat $SP/panda_server-*.dist-info/direct_url.json
diff <(sort /opt/panda-backup-<date>/pip-freeze.txt) <(/opt/panda/bin/pip freeze | sort)
```

Expected: `No broken requirements found`; `direct_url.json` names the target commit; the freeze diff shows only the panda-server, panda-common and (removed) panda-jedi lines. The ePIC modules, pinned, with no dependencies:

```
sudo /opt/panda/bin/pip install --no-deps "swf-epicprod @ git+https://github.com/BNLNPPS/swf-epicprod.git@<commit>" > /tmp/pip-install-swf-epicprod.log 2>&1
sudo /opt/panda/bin/pip check
```

The services keep running the old code from memory until step 7; keep the gap short.

### 6. Configuration

Diff each new template against the previous one in the copy; expected: only the changes the assessment found.

```
B=/opt/panda-backup-<date>/etc/panda; L=/opt/panda/etc/panda
for f in panda_common.cfg panda_jedi.cfg panda_server.cfg panda_server-httpd.conf; do echo "-- $f"; diff $B/$f.rpmnew $L/$f.rpmnew; done
```

Apply each change that applies here to the live file by script (Rules, 1), after a dated backup of the file: `sudo cp -p $L/<file> $L/<file>-backup-<date>`. Print the changed line and `diff` the backup against the live file. For the httpd configuration, `sudo httpd -t -f $L/panda_server-httpd.conf` must print `Syntax OK` before the restart. Database configuration rows go in from a `.sql` file: `PGPASSWORD="$(sudo grep '^dbpasswd' /etc/panda/panda_server.cfg | sed 's/^dbpasswd *= *//')" psql -h pandadb01.sdcc.bnl.gov -U panda -d panda_db -v ON_ERROR_STOP=1 -f /tmp/upgrade-<date>/<file>.sql`, the file ending with a `SELECT` that prints the rows back; the `INSERT` and its `DELETE` go into the change log.

If a unit or logrotate template changed in the assessment, apply and `sudo systemctl daemon-reload` now. If none changed, the units are byte-identical after the install (verify: `diff /opt/panda-backup-<date>/etc/panda/systemd/<unit>.service /opt/panda/etc/panda/systemd/<unit>.service` for each) and the `daemon-reload` after the restart only clears systemd's "changed on disk" warning.

### 7. Restart

```
sudo systemctl restart panda panda_httpd panda_daemon panda_jedi panda_mcp; sleep 25
for s in panda panda_httpd panda_daemon panda_jedi panda_mcp; do echo $s $(systemctl is-active $s); done
sudo journalctl --since "2 min ago" -u panda -u panda_jedi --no-pager | grep -i schema
sudo systemctl daemon-reload
```

Expected: five `active`; two lines `DB schema check: OK` (the server's, then JEDI's). Anything else: Reversibility.

### 8. Verification

```
curl -s -o /dev/null -w "%{http_code}\n" http://pandaserver01.sdcc.bnl.gov:25080/api/v1/system/is_alive        # 200
for f in /var/log/panda/panda_daemon_stderr.log /var/log/panda/panda_jedi_stderr.log /var/log/panda/panda_mcp_stderr.log; do sudo grep -c Traceback $f; done   # 0 0 0
sudo grep -c Traceback /var/log/panda/panda_server_error_log                                                # 0 since the restart
ps -u atlpan -o pid,etimes,args | grep JediMaster | grep -v grep | wc -l                                      # several, young
sudo grep "is ready for" /var/log/panda/panda-JobThrottler.log | tail -4        # the registered throttler class, per VO
sudo tail -12 /var/log/panda/panda-EpicProdJobThrottler.log                     # a reading per generation cycle
```

The access log since the restart, by status (the log is UTC; adjust the pattern to the restart time):

```
sudo awk '/16\/Sep\/2026:20:0[3-9]|16\/Sep\/2026:2[0-3]:[1-5]/' /var/log/panda/panda_server_access_log > /tmp/upgrade-<date>/access-since-restart.log
grep -oE '" [0-9]{3} ' /tmp/upgrade-<date>/access-since-restart.log | sort | uniq -c
grep -vE '" (200|304) ' /tmp/upgrade-<date>/access-since-restart.log | tail
```

Expected: all 200 and 304 (the legacy `/server/panda/isAlive` answers 403 by design; do not read it as a failure). From the monitor: harvester workers keep appearing (`panda_harvester_workers`), running jobs keep heartbeating (`panda_list_jobs` status running, modificationtime advancing), and a canary task on a production queue runs to completion. The fix that motivated the upgrade is exercised. An hour of watching; the nightly rotation restart is a second verification when the upgrade runs in the evening.

### 9. Rollback

```
sudo systemctl stop panda_jedi panda_daemon panda_mcp panda_httpd panda
sudo mv /opt/panda /opt/panda-failed-<date>
sudo cp -a /opt/panda-backup-<date> /opt/panda
sudo systemctl daemon-reload
sudo systemctl start panda panda_httpd panda_daemon panda_jedi panda_mcp
```

then steps 7's checks and 8 again. Minutes. The copy carries the configuration as it was; the failed tree is kept for the diagnosis.

### 10. Record

Log the upgrade in [CHANGES.md](CHANGES.md): the date, the versions, the configuration changes with their motivation and their reversal, the verification as observed, the rollback copy, and every deviation from the plan. Clear the Pending upgrade section.

## Reversibility

The upgrade is reversible because everything it changes on the host lives under one tree, `/opt/panda`, and the copy of step 4 is that tree entire: the virtual environment, the installed packages, the live configuration files and the previous templates. The virtual environment's own paths name `/opt/panda`, so the copy runs only when restored to that path, which is what the rollback does. What the upgrade touches outside the tree, and how each is reversed:

| Outside the tree | Reversal |
|---|---|
| Database schema | Nothing while the minimum schema is unchanged: the code writes no schema, and the rollback needs no database action. An upgrade with a schema change is a different procedure: the database patch and its reverse are written into the Pending upgrade section before execution, and the copy alone is no longer the rollback. |
| `DOMA_PANDA.config` rows for an ePIC module | Inert without the module: the restored tree has no `swf_epicprod` and registers the generic plugin, which never reads them. Removed only if wanted, by the `DELETE` recorded in the change log beside the `INSERT`. |
| Logs under `/var/log/panda` | Untouched; a new component's log file is left as a record. |
| Harvester, the pilot, iDDS, the monitor | Clients of the HTTP API only; they retry through the restart either way and hold no state from the upgrade. |
| Jobs and tasks in the database | Unchanged by a restart: tasks in every state (paused, finishing, ready) survive the nightly rotation restart daily, and the throttled and running jobs of the moment are rows. |

The rollback decision is taken on the checks of steps 7 and 8, at any of: a schema check that does not read `OK`; a traceback in a `panda_*_stderr.log` or the JEDI log that recurs across cycles; `is_alive` not answering 200; no harvester worker appearing or no job dispatching within fifteen minutes of the restart on a queue with work; an ePIC module failing to import (JEDI then registers nothing for its VOs and generates no jobs: `panda-JobThrottler.log` names the failure at start). The rollback is executed at once on any of these and diagnosed afterward on the failed tree; it is not attempted in place. A rollback is itself logged in CHANGES.md with its trigger.

## ePIC modules in JEDI

JEDI plugins owned by ePIC production are registered in `panda_jedi.cfg` `modConfig` lines and installed in the virtual environment from the [swf-epicprod](https://github.com/BNLNPPS/swf-epicprod) repository at a pinned commit, with `--no-deps` (the package declares no dependencies, and the JEDI modules import only `pandacommon` and `pandajedi`; a plain install would still pull nothing, the flag states the intent). Each upgrade re-verifies them: `panda-JobThrottler.log` (or the log of the axis the module serves) reports the class `is ready for <vo>:<label>:<subtype>`, and the module writes its own `panda-<Class>.log`. Registered since 2026-09-16: the [ePIC job throttler](https://github.com/BNLNPPS/swf-epicprod/blob/main/docs/EPIC_JOB_THROTTLER.md), for the VOs `wlcg` and `epic`.

Production tasks carry VO `wlcg`: the server was commissioned with the generic JEDI plugins under that key, and the production team's recipe and PCS's Standard Production configuration both submit `vo wlcg`, `prodSourceLabel managed`. The `epic` VO carries the test paths (canary probes, GPU tests, client-API test submissions). JEDI's throttler statistics are per VO, so a module registered for one VO sees only that VO's jobs at a site.

Changes to panda-server itself go to the maintainers as pull requests. The server runs the maintainers' releases or master commits, never a local patch.

## Pending upgrade

None. The September 2026 upgrade was executed 2026-09-16; its plan and its record are in [CHANGES.md](CHANGES.md).

## Record

Executed upgrades are logged in [CHANGES.md](CHANGES.md).

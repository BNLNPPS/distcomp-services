# PanDA server: change log

Every change to the PanDA server and JEDI installation on `pandaserver01.sdcc.bnl.gov`, newest first. An entry records the date, the role that made the change, what changed (package versions with commits, configuration files with the motivation), how it was verified, and the rollback copy. Upgrades follow [UPGRADE.md](UPGRADE.md).

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

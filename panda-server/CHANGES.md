# PanDA server: change log

Every change to the PanDA server and JEDI installation on `pandaserver01.sdcc.bnl.gov`, newest first. An entry records the date, the role that made the change, what changed (package versions with commits, configuration files with the motivation), how it was verified, and the rollback copy. Upgrades follow [UPGRADE.md](UPGRADE.md).

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

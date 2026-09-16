# PanDA server upgrade, 2026-09-16

Executed 16:00 to 16:12 ET on `pandaserver01.sdcc.bnl.gov`, by Torre Wenaus with an AI session, following [panda-server/UPGRADE.md](../panda-server/UPGRADE.md) as it stood at commit 9959968 (the reversibility contract and the VO correction added the same afternoon). Logged in [panda-server/CHANGES.md](../panda-server/CHANGES.md).

## What was done

- panda-server c7109f06 (1.0.0 plus 144 commits, installed 2026-06-07) to master 8f155ac9 (1.0.4 plus the commits through 2026-09-15: the `update_event_ranges` fix e3307c3d, the PostgreSQL subquery-alias fixes #790 and #791, the maintainers' annotation sweep, the workflows4 branch); panda-common 0.1.8 to 0.1.11. Installed under the production `pip freeze` as constraints: no other package moved. The stale `panda_jedi-0.6.4.dist-info` record was removed before the install.
- The ePIC job throttler registered in JEDI for the VOs `wlcg` and `epic` (`panda_jedi.cfg` `[jobthrottle]` `modConfig`), from swf-epicprod pinned at 9f8fbb8, installed with `--no-deps`; `MODE=observe` rows for both VOs in `DOMA_PANDA.config`.
- `panda_server-httpd.conf`: the maintainers' change of 2026-06-16 applied to the jedilog cache block (`Header set Content-Encoding gzip "expr=%{REQUEST_URI} !~ m#\.log$#"`); the local `_gz.out` block of 2026-08-21 unchanged.
- Rollback copy `/opt/panda-backup-2026-09-16`, proven before the install; the previous copies (2026-06-07, 2026-09-14) kept.

## What was seen

- Before: production at rest by design, the day the JLab Rucio catalog collapsed under three 50,000-job tasks; task 39992 finished at 15:29 ET after a three-and-a-half-hour serial kill of its queued jobs, 39994 and 39995 paused; Xin Zhao's EICFast task 40003 with 30 jobs running on BNL_PanDA_1; one canary job waiting at Perlmutter.
- Gate re-run on 8f155ac9 that afternoon: `pip check` clean, 298 modules imported with the four known non-blocking failures, 42 configured targets loaded including the throttler, the event fix present.
- Restart at 16:03:31 ET: all five services active; `DB schema check: OK` at 16:03:36 (server) and 16:03:39 (JEDI); `is_alive` 200; no traceback in the daemon, JEDI or MCP stderr logs or the server error log; JEDI's six `JediMaster.py` processes up; 337 API requests in the first eight minutes all 200 (harvesters, osgsub01, iDDS, the CERN monitor), the one 403 being the legacy `isAlive` path; Xin's jobs kept running and heartbeating; the Perlmutter canary's worker submitted.
- Throttler: `panda-JobThrottler.log` reports `EpicProdJobThrottler ... is ready for wlcg:any:any` and `epic:any:any`; the job generator consults it every cycle; `panda-EpicProdJobThrottler.log` carries readings, e.g. `wlcg:any queue=managed SCORE: BNL_OSG_PanDA_1: room 2000 (bound 2000, queued 0, running 0); OBSERVE would PASS`.
- systemd reported the five unit files changed on disk after the install; they were byte-identical to the copy's; `daemon-reload` cleared the warning.

## Deviations from the plan

1. The plan as first circulated registered the throttler for `epic` alone. Every production task carries `wlcg` (the production recipe and PCS's Standard Production configuration both submit `vo wlcg`); `epic` is the test traffic. Corrected before execution: registered for both VOs, a `MODE` row each.
2. Two inline edits through the two-hop ssh were mangled by shell quoting: the httpd expression lost `\.log$` (caught by `httpd -t`, the conf restored from its backup and edited by a script), and the SQL statement did not parse (rerun from a file). The procedure now requires edits by script and SQL from files.
3. A host-side test import of the throttler created `panda-EpicProdJobThrottler.log` under the operator's user; changed to `atlpan`, mode 666, before JEDI's first write. The procedure now forbids running the server's code on the host as one's own user.
4. The `daemon-reload` was not in the plan; added to the procedure after the restart.

## Outcome

Upgraded and verified. The throttler observes; switching production to throttling is the `wlcg` `MODE` row set to `throttle` with the per-site limits (`NQUEUELIMIT_BNL_OSG_PanDA_1` at the queue's measured ceiling, 3,123 on 2026-09-16), on the production operators' decision. Open beside it: the event-service verification on the BNL_NPPS_GPU test queue (not exercised the same day), and the 79,015 `throttled` rows of the paused tasks 39994 and 39995, which a resume would activate at once and a finish kills serially over hours; the operators' call is finish plus residual rerun, not resume.

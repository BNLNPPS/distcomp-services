# ePIC pilot builds: change log

Since 2026-10-02 `UM_GREX_PanDA_1` and `BNL_OSG_EPIC_PROD_1` run the pilot published in the production team's canary directory, `/cvmfs/eic.opensciencegrid.org/panda/pilot/canary/pilot3.tar.gz`, a symlink to one build, named by `--piloturl` in their submit descriptions; `BNL_OSG_PanDA_1` keeps the shared template and the pilot its CRIC record names (upstream 3.14.3.3 on 2026-10-29, without the Event Service fix of PanDAWMS/pilot3#220). A build is upstream PanDAWMS/pilot3 plus ePIC changes, built from a branch of `wenaus/pilot3`. The publication procedure and its record are in swf-epicprod `docs/OSG_SUBMISSION.md` (Our canary pilot directory). This log lists each build and tracks every change it carries to its upstream pull request, newest first. Pull requests to PanDAWMS/pilot3 target its `next` branch. Every change to PanDA code goes upstream (Torre, 2026-10-29).

## Changes carried and their upstream status

| Change | Branch | In builds | Upstream |
|---|---|---|---|
| Log stage-out fallback: a log whose transfer failed is held through the PCS log-grant service, without failing the job (4 commits, 2026-10-02) | `epic-log-fallback` | epic5 | open: PanDAWMS/pilot3#229 from `epic-log-fallback-next`, the same change on upstream `next`, tested and opened 2026-10-30 |
| epic plugin uses the ePIC Rucio configuration when the environment names none (2026-10-02) | `epic-rucio-config` | epic5 | open: PanDAWMS/pilot3#230 from `epic-rucio-config-next`, the same change on upstream `next`, tested and opened 2026-10-30 |
| Transfer errors: every exception passes through the timers; authentication and server failures are named (2026-10-02) | `epic-transfer-errors` | epic5 | open: PanDAWMS/pilot3#231 from `epic-transfer-errors-next`, the same change on upstream `next`, tested and opened 2026-10-30 |
| The server's debug mode exported to the payload as a file in the work directory (4 commits, 2026-09-24) | `epic-debug-mode-file` | epic5 | merged in a revised form, PanDAWMS/pilot3#224 from `epic-debug-mode-file-next`; the build carries the earlier form |
| Event Service: the server's api/v1 event methods; ES stage-out client construction | `epic-es-server-api-v1` | epic4, epic5 | merged, PanDAWMS/pilot3#221 |
| Event Service payload command built with the pilot arguments | `epic-es-payload-command-args` | epic4, epic5 | merged, PanDAWMS/pilot3#220 |
| epic: payload event counts and declared metrics lifted into the job record | `epic-nevents-from-report` | epic4, epic5 | merged, PanDAWMS/pilot3#217 |
| epic: payload job report errors lifted into the job record | `epic-jobreport-lift` | epic4, epic5 | merged, PanDAWMS/pilot3#212 |

## 2026-10-02: build epic5 published (found 2026-10-29)

- `pilot3-3.14.3.3-epic5.tar.gz`, branch `epic-build-5` (merge base with upstream master 2026-09-09), the canary symlink's target since 2026-10-02. Recorded here on 2026-10-29 by Claude swf-1 from the canary directory and the branch; the publication itself is recorded in swf-epicprod `docs/OSG_SUBMISSION.md`.
- Earlier builds in the directory: epic4 (2026-10-01), epic1 (2026-09-09), and the upstream releases 3.14.2.2 and 3.14.1.31.

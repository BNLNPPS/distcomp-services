# PanDA monitor: change log

Every change to the PanDA monitor (panda-bigmon-core) on `pandamon01.sdcc.bnl.gov`, newest first. The code lives in `/data/bigmon/core`, not a git checkout, beside dated copies (`core-backup-*`, `core-new-from-github`); its virtual environment is `/opt/bigmon`. Reached from swf-testbed through the SCDF gateway like pandaserver01: `ssh -A -o BatchMode=yes wenauseic@ssh.sdcc.bnl.gov "ssh -o BatchMode=yes pandamon01 '<command>'"`. Every change to the monitor's code goes upstream to PanDAWMS/panda-bigmon-core (Torre, 2026-10-29).

## Local changes on the host

| File | Change | Since | Upstream |
|---|---|---|---|
| `libs/exlib.py` | the per-core memory limit is computed only when the queue record holds numeric `maxrss` and a positive `corecount` (a missing or zero value raised) | 2026-09-29 | fixed upstream: PanDAWMS/panda-bigmon-core#689, merged 2026-09-30, refuses the zero core count that raised here. The patch's further type checks address no recorded failure and are not proposed; the patch is dropped at the next update from upstream |
| `cachecontroller/settingscron.py` | site settings: `BASE_URL` the BNL monitor, the BNL filebrowser path, five days of logs | 2026-03-02 | site configuration, not for upstream |
| `settings/config.py` | site settings | 2026-07-15 | site configuration, not for upstream |

## 2026-10-29: local changes found on the host

- By: Claude swf-1, read only. Source files of `/data/bigmon/core` changed since 2026-01-01, by modification time: the three above; dated backups beside two of them (`exlib.py-backup-2026-09-29`, `settingscron.py-backup-2026-03-02`). Who made them is not recorded on the host. The code was last replaced wholesale on 2025-12-02 (`core-new`); a comparison of the whole tree with an upstream release is not yet done.

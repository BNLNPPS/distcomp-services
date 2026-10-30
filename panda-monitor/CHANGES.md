# PanDA monitor: change log

Every change to the PanDA monitor (panda-bigmon-core) on `pandamon01.sdcc.bnl.gov`, newest first. The code lives in `/data/bigmon/core`, not a git checkout; its dated copies (`core-backup-*`, `core-new-from-github`) were moved on 2026-10-30 to `/data2/bigmon-app-backup-2026-10-30`, by PanDA operations at BNL. Its virtual environment is `/opt/bigmon`. Reached from swf-testbed through the SCDF gateway like pandaserver01: `ssh -A -o BatchMode=yes wenauseic@ssh.sdcc.bnl.gov "ssh -o BatchMode=yes pandamon01 '<command>'"`. Every change to the monitor's code goes upstream to PanDAWMS/panda-bigmon-core (Torre, 2026-10-29).

## Local changes on the host

The installed tree is PanDAWMS/panda-bigmon-core commit `e01c8b82` (2025-11-25, nine commits after v0.7.7) except for the files of this table. [audit/installed_blobs.py](audit/installed_blobs.py) with [audit/nearest_commit.py](audit/nearest_commit.py) finds that commit and must name exactly these files; the other files not in the commit are dated backups and editor copies (`*-backup-*`, `*~`), and `settings/local.py` is a link to `/data/bigmon/config/local.py`.

```
ssh ... "ssh pandamon01 '/opt/bigmon/bin/python3 -I -'" < audit/installed_blobs.py > /tmp/installed.json
python3 audit/nearest_commit.py /tmp/installed.json <panda-bigmon-core checkout>
```

| File | Change | Since | Upstream |
|---|---|---|---|
| `libs/exlib.py` | the per-core memory limit is computed only when the queue record holds numeric `maxrss` and a positive `corecount` (a missing or zero value raised) | 2026-09-29 | fixed upstream: PanDAWMS/panda-bigmon-core#689, merged 2026-09-30, refuses the zero core count that raised here. The patch's further type checks address no recorded failure and are not proposed; the patch is dropped at the next update from upstream |
| `cachecontroller/settingscron.py` | site settings: `BASE_URL` the BNL monitor, the BNL filebrowser path, five days of logs | 2026-03-02 | site configuration, not for upstream |
| `settings/config.py` | site settings | 2026-07-15 | site configuration, not for upstream |

## 2026-10-30: installed tree compared with upstream

- By: Claude swf-1, read only. Of 815 installed files, 807 match commit `e01c8b82` exactly, more than any other commit of `main` that touched `core/`. The three files of the table differ from it; five dated backups and editor copies are the other files it does not have; none of its files is absent. Upstream `main` is 365 commits ahead, at 1.2.7 (2026-10-27). No local code change is outstanding: `libs/exlib.py` is fixed upstream and the other two are site settings.

## 2026-10-29: local changes found on the host

- By: Claude swf-1, read only. Source files of `/data/bigmon/core` changed since 2026-01-01, by modification time: the three above; dated backups beside two of them (`exlib.py-backup-2026-09-29`, `settingscron.py-backup-2026-03-02`). Who made them is not recorded on the host. The code was last replaced wholesale on 2025-12-02 (`core-new`); the comparison of the whole tree with upstream followed on 2026-10-30.

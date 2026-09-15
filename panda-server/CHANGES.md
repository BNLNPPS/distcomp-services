# PanDA server: change log

Every change to the PanDA server and JEDI installation on `pandaserver01.sdcc.bnl.gov`, newest first. An entry records the date, the role that made the change, what changed (package versions with commits, configuration files with the motivation), how it was verified, and the rollback copy. Upgrades follow [UPGRADE.md](UPGRADE.md).

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

# osgsub01 changes

Newest first.

## 2026-10-28: pilot-log retention

- **By:** ePIC production operations (swf-1), on Torre Wenaus's word.
- **What:** at 00:46 ET a one-off pass gzipped the pilot logs idle 6 hours and
  not named by a queued job: 394,824 files, 447 GB before compression (list
  and log in `/var/log/epicprod-pilot-log-gzip/20261028T044649Z.*`). Then
  `pilot-log-retention.py` was installed with an hourly cron entry as
  `atlpan`: compress after 6 hours, remove hour directories after 6 days
  ([README.md](README.md#pilot-log-retention)).
- **Why:** `/var` was at 92%, 42 GB free of 520 GB; 437 GB of it was pilot
  logs back to 21 October, rotated by nothing.
- **Verified:** the installer's `--dry-run` as `atlpan`, then the first
  hourly run's line in `retention.log`.
- **Rollback:** `./install-pilot-log-retention.sh --remove` stops it;
  `gunzip` restores a compressed log. Removed logs are not recoverable.

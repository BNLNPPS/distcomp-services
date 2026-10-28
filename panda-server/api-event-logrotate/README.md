# PanDA event API log rotation

The PanDA server writes every Event Service range it hands out and every range
reported back to `/var/log/panda/panda-api_event.log`, at DEBUG: the level is
global (`log_level=DEBUG` in `/etc/panda/panda_common.cfg`) and the event API's
logger (`api_event`, `pandaserver/api/v1/event_api.py`) has none of its own.
The package's logrotate entry rotates all of `/var/log/panda/*log` once a day,
keeps 10, and restarts JEDI and the server in its postrotate; that is the
nightly restart. On 28 October 2026 the event log grew about 5.8 GB a day with
one Perlmutter node and Google on 10-event ranges, against 16 GB free on
`/var`; five Perlmutter nodes would fill `/var` between nightly rotations.

[`panda-api-event.logrotate`](panda-api-event.logrotate) rotates that one log
when it passes 2 GB, checked hourly by cron, with `copytruncate`, so no restart
and the DEBUG detail is kept. Rotated copies are compressed (about 4% of their
size) into `/var/log/panda/api_event/` and kept six days, outside the daily
entry's reach. The daily entry still rotates what remains each night.

Install or update from swf-testbed, after committing: `./install.sh`. It
copies the entry to `/etc/panda/panda-api-event.logrotate`, creates the
archive directory, shows logrotate's dry run, and writes
`/etc/cron.d/panda-api-event-logrotate` (minute 7, own state file
`/var/lib/logrotate/panda-api-event.status`). `./install.sh --remove` removes
the cron entry.

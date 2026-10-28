#!/bin/bash
# Install the size-triggered rotation of the PanDA event API log on
# pandaserver01: the logrotate entry in /etc/panda, its archive directory,
# and an hourly cron entry running logrotate on it with its own state file.
# Run from swf-testbed, in this directory:  ./install.sh  |  ./install.sh --remove
# --remove deletes the cron entry only; rotated copies stay.
set -euo pipefail
cd "$(dirname "$0")"
HOST=pandaserver01
CONF=/etc/panda/panda-api-event.logrotate
CRON=/etc/cron.d/panda-api-event-logrotate
STATE=/var/lib/logrotate/panda-api-event.status
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST")

if [[ "${1:-}" == "--remove" ]]; then
    "${SSH[@]}" "sudo -n rm -f $CRON && echo removed $CRON"
    exit 0
fi
[[ -z "$(git status --porcelain -- panda-api-event.logrotate)" ]] || {
    echo "panda-api-event.logrotate has uncommitted changes; commit first" >&2; exit 1; }
commit=$(git rev-parse --short HEAD)

"${SSH[@]}" "sudo -n install -d -o atlpan -g atlpan -m 755 /var/log/panda/api_event"
"${SSH[@]}" "sudo -n tee $CONF.new >/dev/null" < panda-api-event.logrotate
"${SSH[@]}" "sudo -n bash -c 'chmod 644 $CONF.new && chown root:root $CONF.new && mv -f $CONF.new $CONF'"
"${SSH[@]}" "sudo -n /usr/sbin/logrotate -d -s $STATE $CONF 2>&1 | tail -6"
"${SSH[@]}" "sudo -n tee $CRON >/dev/null" <<CRONEOF
# PanDA event API log, size-triggered rotation without a restart (distcomp-services $commit)
7 * * * * root /usr/sbin/logrotate -s $STATE $CONF
CRONEOF
"${SSH[@]}" "sudo -n chmod 644 $CRON && cat $CRON"

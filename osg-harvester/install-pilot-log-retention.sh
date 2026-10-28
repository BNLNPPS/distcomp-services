#!/bin/bash
# Install pilot-log-retention.py on osgsub01 and run it hourly as atlpan.
# Run from the operating account on swf-testbed, in this directory:
#   ./install-pilot-log-retention.sh            # install and enable
#   ./install-pilot-log-retention.sh --remove   # remove the cron entry only
# The script, its COMMIT and its run log live in
# /var/data/atlpan/harvester_common/pilot-log-retention/ on the host.
set -euo pipefail
cd "$(dirname "$0")"
HOST=osgsub01
DEST=/var/data/atlpan/harvester_common/pilot-log-retention
CRON=/etc/cron.d/epicprod-pilot-log-retention
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST")

if [[ "${1:-}" == "--remove" ]]; then
    "${SSH[@]}" "sudo -n rm -f $CRON && echo removed $CRON"
    exit 0
fi

python3 -m py_compile pilot-log-retention.py
commit=$(git rev-parse --short HEAD)
[[ -z "$(git status --porcelain -- pilot-log-retention.py)" ]] || {
    echo "pilot-log-retention.py has uncommitted changes; commit first" >&2; exit 1; }

"${SSH[@]}" "sudo -n install -d -o atlpan -g atlpan -m 755 $DEST"
"${SSH[@]}" "sudo -n tee $DEST/pilot-log-retention.py.new >/dev/null" < pilot-log-retention.py
"${SSH[@]}" "sudo -n bash -c 'chown atlpan:atlpan $DEST/pilot-log-retention.py.new &&
  chmod 755 $DEST/pilot-log-retention.py.new &&
  mv -f $DEST/pilot-log-retention.py.new $DEST/pilot-log-retention.py &&
  echo $commit > $DEST/COMMIT && chown atlpan:atlpan $DEST/COMMIT'"
"${SSH[@]}" "sudo -n -u atlpan /usr/bin/python3 $DEST/pilot-log-retention.py --dry-run"
"${SSH[@]}" "sudo -n tee $CRON >/dev/null" <<EOF
# epicprod pilot-log retention (distcomp-services osg-harvester, $commit)
17 * * * * atlpan nice -n 19 ionice -c3 /usr/bin/python3 $DEST/pilot-log-retention.py >/dev/null 2>&1
EOF
"${SSH[@]}" "sudo -n chmod 644 $CRON && cat $CRON"

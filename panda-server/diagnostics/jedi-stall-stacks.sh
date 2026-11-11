#!/bin/bash
# Capture the Python stacks of a stalled JEDI PostProcessor on pandaserver01.
#
# The PostProcessor's prepareTasksToBeFinished_JEDI call intermittently hangs in
# its task-buffer child until JEDI's 600 s timeout kills it (JEDITimeoutError in
# panda_jedi_stdout.log). This script waits, from swf-testbed, for the next stall:
# panda-PostProcessor.log unchanged for more than QUIET_S seconds. It then takes
# `thread apply all py-bt` of the PostProcessor launcher process and of JEDI's
# task-buffer children (jedi-stall-stacks-remote.sh, shipped with CPython's gdb
# helper for the host's Python, 3.11.6), and exits after one capture. Read-only
# on the host: gdb pauses each process for the seconds the backtrace takes; the files shipped to /tmp on the host are removed afterwards.
#
# Usage: jedi-stall-stacks.sh OUTPUT_FILE [HOURS] [QUIET_S]
#   OUTPUT_FILE  where the stacks are written (on swf-testbed)
#   HOURS        how long to wait for a stall (default 24)
#   QUIET_S      log silence that counts as a stall (default 200)
# Run in the background; it checks the log age once a minute.
set -u
OUT=${1:?usage: jedi-stall-stacks.sh OUTPUT_FILE [HOURS] [QUIET_S]}
HOURS=${2:-24}
QUIET_S=${3:-200}
PY_TAG=v3.11.6
CACHE=${XDG_CACHE_HOME:-$HOME/.cache}/distcomp-services
LIB=$CACHE/libpython-$PY_TAG.py
HERE=$(cd "$(dirname "$0")" && pwd)
SSH=(ssh -A -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 wenauseic@ssh.sdcc.bnl.gov)
HOP='ssh -o BatchMode=yes -o StrictHostKeyChecking=no pandaserver01'

if [ ! -s "$LIB" ]; then
  mkdir -p "$CACHE"
  curl -sf --max-time 60 -o "$LIB.tmp" "https://raw.githubusercontent.com/python/cpython/$PY_TAG/Tools/gdb/libpython.py" \
    && mv "$LIB.tmp" "$LIB" || { echo "cannot fetch CPython $PY_TAG gdb helper" >&2; exit 1; }
fi

end=$(( $(date +%s) + HOURS*3600 ))
echo "$(date) waiting up to $HOURS h for panda-PostProcessor.log to be quiet > $QUIET_S s"
while [ "$(date +%s)" -lt "$end" ]; do
  age=$(timeout 60 "${SSH[@]}" "$HOP 'echo \$(( \$(date +%s) - \$(stat -c %Y /var/log/panda/panda-PostProcessor.log) ))'" 2>/dev/null | tail -1)
  if [[ "$age" =~ ^[0-9]+$ ]] && [ "$age" -gt "$QUIET_S" ]; then
    stage=$(mktemp -d)
    cp "$LIB" "$stage/libpython.py"; cp "$HERE/jedi-stall-stacks-remote.sh" "$stage/remote.sh"
    tar -C "$stage" -cz libpython.py remote.sh \
      | timeout 900 "${SSH[@]}" "$HOP 'D=\$(mktemp -d /tmp/jedi-stacks.XXXXXX); tar -xz -C \$D && LOG_AGE=$age bash \$D/remote.sh; rm -rf \$D'" > "$OUT" 2>&1
    rm -rf "$stage"
    echo "$(date) captured at log_age=$age -> $OUT"
    exit 0
  fi
  sleep 60
done
echo "$(date) no stall within $HOURS h"
exit 2

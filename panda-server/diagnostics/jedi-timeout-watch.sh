#!/bin/bash
# Watch pandaserver01's JEDI log for a JEDITimeoutError after a given time.
#
#   jedi-timeout-watch.sh SINCE_UTC UNTIL_UTC [INTERVAL_SECONDS]
#   e.g. jedi-timeout-watch.sh "2026-11-12 17:26:33" "2026-11-13 05:30:00" 600
#
# Every INTERVAL seconds (default 600) it reads the timeouts in
# /var/log/panda/panda_jedi_stdout.log (and its .1 rotation) through the SCDF
# gateway. It prints and exits 1 at the first timeout stamped after SINCE_UTC,
# exits 0 with "none" once UNTIL_UTC passes, and exits 2 after three
# consecutive failed reads. The log's stamps are UTC.
set -u
since=$1 until=$2 interval=${3:-600}
read_timeouts() {
  timeout 120 ssh -A -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
    wenauseic@ssh.sdcc.bnl.gov \
    "ssh -o BatchMode=yes -o StrictHostKeyChecking=no pandaserver01 'sudo grep -h JEDITimeoutError /var/log/panda/panda_jedi_stdout.log.1 /var/log/panda/panda_jedi_stdout.log 2>/dev/null; echo READ_OK'"
}
fails=0
while :; do
  out=$(read_timeouts)
  if [[ $out != *READ_OK* ]]; then
    fails=$((fails + 1))
    echo "$(date -u '+%F %T') read failed ($fails)" >&2
    [[ $fails -ge 3 ]] && { echo "watch stopped: three failed reads"; exit 2; }
  else
    fails=0
    hit=$(awk -v s="$since" 'substr($0,1,19) > s' <<<"$out" | grep JEDITimeoutError | head -1)
    if [[ -n $hit ]]; then
      echo "TIMEOUT after $since UTC:"
      echo "$hit" | cut -c1-200
      exit 1
    fi
    echo "$(date -u '+%F %T') no timeout after $since UTC"
  fi
  [[ $(date -u '+%F %T') > $until ]] && { echo "none between $since and $until UTC"; exit 0; }
  sleep "$interval"
done

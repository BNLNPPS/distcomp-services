#!/bin/bash
# Host side of jedi-stall-stacks.sh, run on pandaserver01 from the directory it was
# unpacked into (with libpython.py beside it). Prints the Python stacks of the
# PostProcessor launcher and of every single-threaded JediMaster process: the
# task-buffer children are one pool shared by all components, and a child that
# replaces a timed-out one is forked by the component that made the call, so the
# child serving the PostProcessor is not necessarily its own child.
cd "$(dirname "$0")"
LIB=$PWD/libpython.py
bt() {
  sudo timeout 60 gdb -p "$1" -batch -ex "source $LIB" -ex "thread apply all py-bt" 2>&1 \
    | grep -v '^\[New LWP\|Missing separate\|^Try: yum\|^$\|^warning: \|^Using host libthread_db\|^\[Thread debugging'
}
date -u
echo "log_age=${LOG_AGE:-?}"
pp=$(sudo grep -F "PostProcessor: INFO    start launcher with pid=" /var/log/panda/panda_jedi_stdout.log | tail -1 | sed 's/.*pid=//')
echo "postprocessor=$pp"
sudo grep JEDITimeoutError /var/log/panda/panda_jedi_stdout.log | tail -3
ps -u atlpan -o pid,ppid,etime,nlwp,stat,wchan:20,args --forest | grep -E 'JediMaster|PID' | cut -c1-90
echo "=== POSTPROCESSOR $pp"
bt "$pp"
for p in $(ps -u atlpan -o pid=,nlwp=,args= | awk '$2==1 && /JediMaster/ {print $1}'); do
  echo "=== CHILD $p $(ps -o ppid=,etime= -p "$p")"
  bt "$p"
done

#!/usr/bin/env python3
"""Pilot-log retention on osgsub01: compress after hours, delete after days.

Harvester writes each OSG pilot's stdout (.out), stderr (.err) and condor
user log (.log) under LOG_ROOT, one directory per submission hour
(YY-MM-DD_HH), served at the queue's logBaseURL. Nothing else rotates them.
Each run:

1. gzips every .out, .err and .log file in an hour directory that has not
   changed for --compress-hours and belongs to no job in the condor queue;
2. removes every hour directory whose newest file is older than
   --delete-days, unless a job still in the queue names a file in it.

Named directories (trial and cohort evidence) are never touched. A queue
listing that fails stops the run before anything changes. Runs as atlpan
from cron, one run at a time, appending one JSON line per run to the log.
--dry-run reports what a run would do and changes nothing. Python 3.6.
"""
import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import time

LOG_ROOT = '/var/data/atlpan/condor_logs'
HOME = '/var/data/atlpan/harvester_common/pilot-log-retention'
RUN_LOG = os.path.join(HOME, 'retention.log')
LOCK = os.path.join(HOME, '.lock')
HOUR_DIR = re.compile(r'^\d{2}-\d{2}-\d{2}_\d{2}$')
SUFFIXES = ('.out', '.err', '.log')
BATCH = 200


def queued_paths():
    """Real paths of every file a job in the queue names, and their directories."""
    out = subprocess.check_output(
        ['condor_q', '-allusers', '-af', 'UserLog', 'Out', 'Err'],
        universal_newlines=True, timeout=300)
    files, dirs = set(), set()
    for line in out.splitlines():
        for path in line.split():
            if path and path != 'undefined':
                real = os.path.realpath(path)
                files.add(real)
                dirs.add(os.path.dirname(real))
    return files, dirs


def hour_dirs():
    for name in sorted(os.listdir(LOG_ROOT)):
        path = os.path.join(LOG_ROOT, name)
        if HOUR_DIR.match(name) and os.path.isdir(path) and not os.path.islink(path):
            yield path


def scan(path):
    """(files with their stat, newest mtime) under one hour directory."""
    entries, newest = [], 0.0
    for dirpath, _, names in os.walk(path):
        for name in names:
            p = os.path.join(dirpath, name)
            try:
                st = os.lstat(p)
            except OSError:
                continue
            if not os.path.isfile(p) or os.path.islink(p):
                continue
            entries.append((p, st))
            newest = max(newest, st.st_mtime)
    return entries, newest


def run(compress_hours, delete_days, dry_run):
    now = time.time()
    live_files, live_dirs = queued_paths()
    compress_cut = now - compress_hours * 3600
    delete_cut = now - delete_days * 86400
    report = {'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
              'dry_run': dry_run, 'compress_hours': compress_hours,
              'delete_days': delete_days, 'queued_files': len(live_files),
              'deleted_dirs': 0, 'deleted_bytes': 0, 'kept_for_queued_jobs': 0,
              'compressed': 0, 'compressed_bytes_before': 0, 'compress_failures': 0}
    to_compress = []
    for path in hour_dirs():
        entries, newest = scan(path)
        if entries and newest < delete_cut:
            if any(d == path or d.startswith(path + os.sep) for d in live_dirs):
                report['kept_for_queued_jobs'] += 1
            else:
                report['deleted_dirs'] += 1
                report['deleted_bytes'] += sum(st.st_size for _, st in entries)
                if not dry_run:
                    shutil.rmtree(path)
                continue
        for p, st in entries:
            if (p.endswith(SUFFIXES) and st.st_mtime < compress_cut
                    and os.path.realpath(p) not in live_files):
                to_compress.append(p)
                report['compressed_bytes_before'] += st.st_size
    report['compressed'] = len(to_compress)
    if not dry_run:
        for i in range(0, len(to_compress), BATCH):
            batch = to_compress[i:i + BATCH]
            result = subprocess.run(['gzip', '--'] + batch, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode:
                report['compress_failures'] += len(
                    [line for line in result.stderr.splitlines() if line.strip()])
    st = os.statvfs(LOG_ROOT)
    report['var_free_gb'] = round(st.f_bavail * st.f_frsize / 1e9, 1)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--compress-hours', type=float, default=6.0)
    parser.add_argument('--delete-days', type=float, default=6.0)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.compress_hours < 1 or args.delete_days < 1:
        parser.error('--compress-hours and --delete-days must be at least 1')
    os.makedirs(HOME, exist_ok=True)
    with open(LOCK, 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print(json.dumps({'skipped': 'another run holds the lock'}))
            return
        try:
            report = run(args.compress_hours, args.delete_days, args.dry_run)
        except Exception as exc:
            report = {'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                      'error': '%s: %s' % (type(exc).__name__, exc)}
        line = json.dumps(report)
        print(line)
        if not args.dry_run:
            with open(RUN_LOG, 'a') as f:
                f.write(line + '\n')
        if 'error' in report:
            sys.exit(1)


if __name__ == '__main__':
    main()

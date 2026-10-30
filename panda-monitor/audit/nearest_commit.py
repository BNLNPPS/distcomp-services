#!/usr/bin/env python3
"""Find the upstream commit an installed monitor tree came from, and list what differs.

The monitor on pandamon01 is a copy of panda-bigmon-core's `core/`, not a git
checkout, and records no commit. installed_blobs.py, run there, prints the git
blob hash of every installed file. This reads that output beside a
panda-bigmon-core checkout, scores every commit of the branch that touched
`core/` by the number of installed files matching it exactly, and lists, for
the best commit, every installed file that differs from it, every file it does
not have, and every file of it that is absent. Each difference is a change made
on the host or a file the deployment adds; each must be one listed in
CHANGES.md (Local changes on the host).

    ssh ... "ssh pandamon01 'python3 -I -'" < installed_blobs.py > installed.json
    nearest_commit.py installed.json <panda-bigmon-core checkout> [branch]
"""
import json
import subprocess
import sys


def git(checkout, *args):
    return subprocess.run(['git', '-C', checkout, *args], capture_output=True, text=True, check=True).stdout


def tree(checkout, commit):
    out = git(checkout, 'ls-tree', '-r', commit, '--', 'core')
    return {line.split('\t', 1)[1][len('core/'):]: line.split()[2] for line in out.splitlines()}


def main():
    installed = json.load(open(sys.argv[1]))
    checkout = sys.argv[2]
    branch = sys.argv[3] if len(sys.argv) > 3 else 'origin/main'
    files = installed['files']
    scores = []
    for line in git(checkout, 'rev-list', '--format=%h %ad', '--date=short', branch, '--', 'core').splitlines():
        if line.startswith('commit '):
            commit = line.split()[1]
            continue
        t = tree(checkout, commit)
        scores.append((sum(1 for p, h in files.items() if t.get(p) == h), line, commit))
    best = max(scores)
    ties = [s for s in scores if s[0] == best[0]]
    print(f'{len(files)} installed files; best commit {best[1]}: {best[0]} match exactly; '
          f'{len(ties)} commits share that score: {ties[-1][1]} to {ties[0][1]}')
    for tag in git(checkout, 'tag', '--points-at', best[2]).split():
        print('tag', tag)
    t = tree(checkout, best[2])
    differs = sorted(p for p, h in files.items() if p in t and t[p] != h)
    extra = sorted(p for p in files if p not in t)
    absent = sorted(p for p in t if p not in files)
    print(f'{len(differs)} differ from it, {len(extra)} not in it, {len(absent)} of it absent')
    for p in differs:
        print('DIFFERS', files[p], p)
    for p in extra:
        print('EXTRA  ', files[p], p)
    for p in absent:
        print('ABSENT ', p)
    for p, target in sorted(installed.get('links', {}).items()):
        print('LINK   ', p, '->', target)


if __name__ == '__main__':
    main()

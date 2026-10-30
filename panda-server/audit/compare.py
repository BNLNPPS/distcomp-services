#!/usr/bin/env python3
"""Compare an installed PanDA tree with the commit it was installed from.

installed_blobs.py, run on pandaserver01 with the server's Python, prints the
git blob hash of every installed pandaserver and pandajedi file and the
installed commit (direct_url.json). This reads that output beside a
panda-server checkout holding the commit, and lists every installed file that
differs from it, every file the commit does not have, and every file of the
commit that is absent. Each difference is a change made on the host; each must
be one listed in UPGRADE.md (Local changes on the host) before any install.

    ssh ... "ssh pandaserver01 'sudo -n /opt/panda/bin/python -I -'" < installed_blobs.py > installed.json
    compare.py installed.json <panda-server checkout>

The same for Harvester on osgsub01: osg-harvester/audit/installed_blobs.py, whose
output names its packages, compared against a harvester checkout.
"""
import json
import subprocess
import sys


def main():
    installed = json.load(open(sys.argv[1]))
    checkout = sys.argv[2]
    commit = installed['direct_url'].get('vcs_info', {}).get('commit_id')
    print('installed commit:', commit, installed['direct_url'].get('url'))
    packages = installed.get('packages', ['pandaserver', 'pandajedi'])
    out = subprocess.run(['git', '-C', checkout, 'ls-tree', '-r', commit, '--', *packages],
                         capture_output=True, text=True, check=True).stdout
    tree = {line.split('\t', 1)[1]: line.split()[2] for line in out.splitlines()}
    files = installed['files']
    differs = sorted(p for p, h in files.items() if p in tree and tree[p] != h)
    extra = sorted(p for p in files if p not in tree)
    absent = sorted(p for p in tree if p not in files)
    print(f'{len(files)} installed files: {len(differs)} differ from the commit, '
          f'{len(extra)} not in it, {len(absent)} of it absent')
    for p in differs:
        print('DIFFERS', files[p], p)
    for p in extra:
        print('EXTRA  ', files[p], p)
    for p in absent:
        print('ABSENT ', p)


if __name__ == '__main__':
    main()

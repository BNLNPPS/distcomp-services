#!/usr/bin/env python3
"""Install, or roll back, a local patch prepared by prepare.py on pandaserver01.

Run as root with the system Python from the bundle prepare.py wrote, shipped
to /tmp/upgrade-<date>/ (UPGRADE.md, Rules 1):

    host-install.py --bundle <dir> --stamp <UTC stamp>            # dry run
    host-install.py --bundle <dir> --stamp <UTC stamp> --apply
    host-install.py --bundle <dir> --stamp <UTC stamp> --rollback

Installs file by file, never a package: each installed file must still read
the manifest's before-checksum, or nothing is written; each is backed up
beside itself as <file>.before-<patch>-<stamp> and replaced with
its owner and mode kept, then read back against the after-checksum. The
record goes to /opt/panda/<patch>-<stamp>/install.json.
Imports no server code. The restarts the manifest names are separate.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

SP = Path('/opt/panda/lib/python3.11/site-packages')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace_keeping_owner(target, content_from):
    st = target.stat()
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix='.' + target.name + '.')
    os.close(fd)
    shutil.copyfile(content_from, tmp)
    os.chown(tmp, st.st_uid, st.st_gid)
    os.chmod(tmp, st.st_mode & 0o7777)
    os.replace(tmp, target)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--stamp', required=True)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--rollback', action='store_true')
    args = ap.parse_args()
    manifest = json.loads((args.bundle / 'manifest.json').read_text())
    suffix = f".before-{manifest['patch']}-{args.stamp}"
    record_dir = Path(f"/opt/panda/{manifest['patch']}-{args.stamp}")
    rows = []
    for name, sums in manifest['files'].items():
        target, new, backup = SP / name, args.bundle / 'files' / name, SP / (name + suffix)
        now = sha256(target)
        if args.rollback:
            ok = backup.exists() and sha256(backup) == sums['before_sha256'] and now == sums['after_sha256']
        else:
            ok = now == sums['before_sha256'] and sha256(new) == sums['after_sha256'] and not backup.exists()
        rows.append({'file': name, 'installed_sha256': now, 'ok': ok})
    print(json.dumps(rows, indent=2))
    if not all(r['ok'] for r in rows):
        sys.exit('ERROR: a file is not in the state this step expects; nothing written')
    if not (args.apply or args.rollback):
        print('dry run: all files in the expected state')
        return
    for name, sums in manifest['files'].items():
        target, new, backup = SP / name, args.bundle / 'files' / name, SP / (name + suffix)
        if args.rollback:
            replace_keeping_owner(target, backup)
            want = sums['before_sha256']
        else:
            shutil.copy2(target, backup)
            st = target.stat()
            os.chown(backup, st.st_uid, st.st_gid)
            replace_keeping_owner(target, new)
            want = sums['after_sha256']
        if sha256(target) != want:
            sys.exit(f'ERROR: {name} reads {sha256(target)} after the write, not {want}')
    record_dir.mkdir(exist_ok=True)
    action = 'rollback' if args.rollback else 'install'
    (record_dir / f'{action}.json').write_text(json.dumps(
        {'patch': manifest['patch'], 'action': action, 'stamp': args.stamp, 'backup_suffix': suffix,
         'files': manifest['files']}, indent=2) + '\n')
    print(f'{action} done: {len(manifest["files"])} files; record {record_dir}/{action}.json')


if __name__ == '__main__':
    main()

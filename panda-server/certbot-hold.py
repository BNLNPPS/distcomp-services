#!/usr/bin/env python3
"""Hold a certbot lineage at an earlier certificate version, or release it.

The BNL hosts' certificates come from InCommon's ACME service through
certbot, run twice a day by SDCC's Puppet (root cron, `certbot certonly
--keep-until-expiring`). On 2026-11-14 and 15 that service reissued them
from SSL.com, which the grid CA set (/etc/grid-security/certificates) does
not trust. This script puts a lineage back on a grid-trusted version and
keeps certbot from replacing it:

  hold <cert-name> <version>
      Checks that <version> verifies against the grid CA set and that its key
      matches. Sets `autorenew = False` in the lineage's renewal configuration
      (certbot's should_autorenew reads it before the ACME renewal-info
      window, so neither `certbot renew` nor `certonly --keep-until-expiring`
      renews). Moves every archive file of a later version to
      /etc/letsencrypt-held/<cert-name>-<stamp>/ (certbot's ensure_deployed
      relinks live to the latest archive version, so a later version left in
      the archive would come back). Points the live links at <version>.

  release <cert-name>
      Moves the most recent held files back into the archive, points the live
      links at the latest version and removes the autorenew setting.

Neither runs a deploy hook: run the host's hook afterwards so the server
reads what the live links name. --dry-run prints the plan and changes
nothing. Run as root. Record: panda-server/CHANGES.md, 2026-11-15.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

LE = '/etc/letsencrypt'
HELD = '/etc/letsencrypt-held'
GRID_CA = '/etc/grid-security/certificates'
KINDS = ('cert', 'chain', 'fullchain', 'privkey')
FILE_RE = re.compile(r'^(cert|chain|fullchain|privkey)(\d+)\.pem$')


def lineage_paths(name):
    return (os.path.join(LE, 'renewal', name + '.conf'),
            os.path.join(LE, 'archive', name),
            os.path.join(LE, 'live', name))


def archive_versions(archive):
    found = {}
    for f in os.listdir(archive):
        m = FILE_RE.match(f)
        if m:
            found.setdefault(int(m.group(2)), set()).add(m.group(1))
    return found


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True)
    return p.returncode, p.stdout.strip()


def check_version(archive, v):
    cert = os.path.join(archive, 'cert%d.pem' % v)
    chain = os.path.join(archive, 'chain%d.pem' % v)
    key = os.path.join(archive, 'privkey%d.pem' % v)
    rc, out = run(['openssl', 'verify', '-no-CAfile', '-CApath', GRID_CA,
                   '-untrusted', chain, cert])
    print('grid CA verify of version %d: %s' % (v, out.splitlines()[-1] if out else rc))
    if rc != 0:
        sys.exit('version %d does not verify against %s; nothing changed' % (v, GRID_CA))
    rc1, cmod = run(['openssl', 'x509', '-noout', '-modulus', '-in', cert])
    rc2, kmod = run(['openssl', 'rsa', '-noout', '-modulus', '-in', key])
    if rc1 or rc2 or cmod != kmod:
        sys.exit('version %d: key does not match certificate; nothing changed' % v)
    rc, out = run(['openssl', 'x509', '-noout', '-issuer', '-enddate', '-in', cert])
    print(out)


def set_autorenew(conf, value, dry):
    """Write `autorenew = <value>` first in [renewalparams]; None removes it."""
    lines = open(conf).read().splitlines(True)
    out, section = [], None
    for ln in lines:
        s = ln.strip()
        if s.startswith('[') and s.endswith(']'):
            section = s[1:-1]
            out.append(ln)
            if section == 'renewalparams' and value is not None:
                out.append('autorenew = %s\n' % value)
            continue
        if section == 'renewalparams' and re.match(r'^autorenew\s*=', s):
            continue
        out.append(ln)
    if 'renewalparams' not in [l.strip()[1:-1] for l in lines if l.strip().startswith('[')]:
        sys.exit('%s has no [renewalparams] section' % conf)
    print('%s: autorenew %s' % (conf, 'removed' if value is None else '= %s' % value))
    if not dry:
        tmp = conf + '.tmp'
        with open(tmp, 'w') as f:
            f.writelines(out)
        shutil.copymode(conf, tmp)
        os.rename(tmp, conf)


def relink(name, live, v, dry):
    for k in KINDS:
        target = os.path.join('..', '..', 'archive', name, '%s%d.pem' % (k, v))
        link = os.path.join(live, k + '.pem')
        print('%s -> %s' % (link, target))
        if not dry:
            tmp = link + '.tmp'
            if os.path.lexists(tmp):
                os.remove(tmp)
            os.symlink(target, tmp)
            os.rename(tmp, link)


def hold(name, v, dry):
    conf, archive, live = lineage_paths(name)
    vs = archive_versions(archive)
    if vs.get(v) != set(KINDS):
        sys.exit('archive has no complete version %d: %s' % (v, sorted(vs.get(v, []))))
    check_version(archive, v)
    later = sorted(x for x in vs if x > v)
    dest = os.path.join(HELD, '%s-%s' % (name, datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
    print('held directory: %s' % dest)
    if not dry:
        os.makedirs(dest, mode=0o700)
        shutil.copy2(conf, os.path.join(dest, os.path.basename(conf)))
    set_autorenew(conf, 'False', dry)
    moved = []
    for x in later:
        for k in sorted(vs[x]):
            f = '%s%d.pem' % (k, x)
            print('move %s/%s -> %s/' % (archive, f, dest))
            if not dry:
                shutil.move(os.path.join(archive, f), os.path.join(dest, f))
            moved.append(f)
    relink(name, live, v, dry)
    if not dry:
        with open(os.path.join(dest, 'hold.json'), 'w') as f:
            json.dump({'cert_name': name, 'held_at_version': v, 'moved': moved,
                       'time': datetime.datetime.now().isoformat()}, f, indent=1)
    print('dry run: nothing changed' if dry else 'held %s at version %d' % (name, v))


def release(name, dry):
    conf, archive, live = lineage_paths(name)
    helds = sorted(d for d in os.listdir(HELD) if d.startswith(name + '-')) if os.path.isdir(HELD) else []
    vs = archive_versions(archive)
    if helds:
        src = os.path.join(HELD, helds[-1])
        rec = json.load(open(os.path.join(src, 'hold.json')))
        for f in rec['moved']:
            if os.path.exists(os.path.join(archive, f)):
                sys.exit('%s already in the archive; nothing changed' % f)
        for f in rec['moved']:
            print('move %s/%s -> %s/' % (src, f, archive))
            if not dry:
                shutil.move(os.path.join(src, f), os.path.join(archive, f))
            m = FILE_RE.match(f)
            vs.setdefault(int(m.group(2)), set()).add(m.group(1))
    latest = max(v for v, k in vs.items() if k == set(KINDS))
    relink(name, live, latest, dry)
    set_autorenew(conf, None, dry)
    print('dry run: nothing changed' if dry else 'released %s' % name)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')
    h = sub.add_parser('hold')
    h.add_argument('cert_name')
    h.add_argument('version', type=int)
    h.add_argument('--dry-run', action='store_true')
    r = sub.add_parser('release')
    r.add_argument('cert_name')
    r.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'hold':
        hold(a.cert_name, a.version, a.dry_run)
    elif a.cmd == 'release':
        release(a.cert_name, a.dry_run)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == '__main__':
    main()

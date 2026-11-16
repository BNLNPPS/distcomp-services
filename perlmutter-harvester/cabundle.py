#!/usr/bin/env python3
"""The Perlmutter harvester's CA bundle: show it, or add certificates to it.

The harvester verifies the PanDA server against `ca_cert` in
panda_harvester.cfg, etc/pki/tls/certs/CA-bundles.pem in the installation.
It reaches the file through the NERSC IRI API, as queueconfig.py does.

    cabundle.py show
    cabundle.py add <file in the same directory> [--apply]

`add` appends every certificate of the named file that the bundle lacks.
It keeps a dated backup beside the bundle and writes through a side file
copied over the live one in place, so the live file keeps its owner and
mode. Then it reads the result back. Without --apply it prints the plan.
"""
import argparse
import datetime
import re
import subprocess
import sys

from queueconfig import Iri

DIR = '/global/common/software/m3763/panda-harvester/etc/pki/tls/certs'
LIVE = DIR + '/CA-bundles.pem'
PEM = re.compile(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', re.S)


def subjects(text):
    out = []
    for p in PEM.findall(text):
        r = subprocess.run(['openssl', 'x509', '-noout', '-subject'], input=p,
                           capture_output=True, text=True)
        out.append(r.stdout.strip() or 'unreadable: ' + r.stderr.strip()[:100])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('action', choices=('show', 'add'))
    ap.add_argument('source', nargs='?')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    iri = Iri()
    text = iri.read(LIVE)
    for s in subjects(text):
        print('in bundle:', s)
    if a.action == 'show':
        return
    if not a.source:
        raise SystemExit('ERROR: add needs a source file name')
    have = {re.sub(r'\s', '', p) for p in PEM.findall(text)}
    new = [p for p in PEM.findall(iri.read(DIR + '/' + a.source)) if re.sub(r'\s', '', p) not in have]
    for s in subjects('\n'.join(new)):
        print('to add:', s)
    if not new or not a.apply:
        return
    new_text = text.rstrip('\n') + '\n' + '\n'.join(new) + '\n'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup, side = f'{LIVE}-backup-{stamp}', f'{LIVE}.upload-{stamp}'
    iri.copy(LIVE, backup)
    if iri.read(backup) != text:
        raise SystemExit(f'ERROR: backup {backup} does not match the live file; nothing else written')
    iri.upload(side, new_text)
    if iri.read(side) != new_text:
        raise SystemExit(f'ERROR: the uploaded {side} does not match; live file untouched')
    try:
        iri.copy(side, LIVE)
    except SystemExit as e:
        # The API's cp preserves times, which only the owner may set; the
        # content is written first and the read-back decides.
        if 'preserving times' not in str(e):
            raise
    iri.remove(side)
    if iri.read(LIVE) != new_text:
        raise SystemExit(f'ERROR: the live file does not read the edit; restore from {backup}')
    print(f'backup {backup}; bundle now holds {len(subjects(new_text))} certificates')


if __name__ == '__main__':
    sys.exit(main())

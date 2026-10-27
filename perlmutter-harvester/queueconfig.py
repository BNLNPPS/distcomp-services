#!/usr/bin/env python3
"""Read or change a queue's settings in the Perlmutter harvester's
panda_queueconfig.json, through the NERSC IRI API (ACCESS.md).

    queueconfig.py show <queue>
    queueconfig.py set <queue> key=value [key=value ...]            # dry run
    queueconfig.py set <queue> key=value [key=value ...] --apply

Values are JSON (`maxWorkers=1000`, `queueStatus="offline"`). A change copies
the live file to panda_queueconfig.json-backup-<UTC stamp> beside it, uploads the
edited file to a side name, copies that over the live file in place (the live
file keeps its owner and mode), removes the side file, and reads the live file
back against the edit. The file must still be the one read at the start, or
nothing is written. The token is read from its file and never printed.
"""
import argparse
import datetime
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

import yaml

TOKEN_FILE = '/data/wguan2/hpc_tokens/nersc_iri_config.yaml'
CONFIG_DIR = '/global/common/software/m3763/panda-harvester/etc/panda'
LIVE = CONFIG_DIR + '/panda_queueconfig.json'


class Iri:
    def __init__(self):
        conf = yaml.safe_load(open(TOKEN_FILE))
        self.base = conf.get('base_url', 'https://api.iri.nersc.gov').rstrip('/')
        self.token = next(v for k, v in conf.items() if 'token' in k.lower() and isinstance(v, str))
        _, res = self.call('GET', '/api/v1/filesystem/resources')
        self.rid = next(r['id'] for r in res if r.get('name') == 'common')

    def call(self, method, endpoint, params=None, body=None, content_type='application/json'):
        url = self.base + endpoint + ('?' + urllib.parse.urlencode(params) if params else '')
        headers = {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/json'}
        if body is not None:
            headers['Content-Type'] = content_type
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                code, text = r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            raise SystemExit(f'ERROR: {method} {endpoint}: HTTP {e.code} {e.read().decode()[:400]}')
        out = json.loads(text) if text else {}
        if isinstance(out, dict) and out.get('task_id'):
            out = self.wait(out['task_id'])
        return code, out

    def wait(self, task_id):
        for _ in range(90):
            _, t = self.call('GET', f'/api/v1/task/{task_id}')
            status = str(t.get('status', '')).lower()
            if status == 'completed':
                return t.get('result')
            if status in ('failed', 'error', 'canceled'):
                raise SystemExit(f'ERROR: task {task_id} {status}: {json.dumps(t)[:400]}')
            time.sleep(2)
        raise SystemExit(f'ERROR: task {task_id} did not complete')

    def fs(self, method, op, **params):
        return self.call(method, f'/api/v1/filesystem/{op}/{self.rid}', params=params)[1]

    def read(self, path):
        out = self.fs('GET', 'view', path=path)['output']
        if out['end_position'] - out['start_position'] != len(out['content'].encode()):
            raise SystemExit(f'ERROR: {path} read incompletely')
        return out['content']

    def stat(self, path):
        return self.fs('GET', 'stat', path=path)['output']

    def copy(self, source, target):
        return self.call('POST', f'/api/v1/filesystem/cp/{self.rid}',
                         body=json.dumps({'path': source, 'target_path': target}).encode())

    def upload(self, path, text):
        boundary = uuid.uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.rsplit("/", 1)[1]}"\r\n'
                f'Content-Type: application/json\r\n\r\n').encode() + text.encode() + f'\r\n--{boundary}--\r\n'.encode()
        return self.call('POST', f'/api/v1/filesystem/upload/{self.rid}', params={'path': path}, body=body,
                         content_type=f'multipart/form-data; boundary={boundary}')

    def remove(self, path):
        return self.fs('DELETE', 'rm', path=path)


def edit_text(text, queue, changes):
    """The file with each named setting of the queue replaced in place: the
    file mixes tabs and spaces, and is not re-serialized."""
    start = text.index(json.dumps(queue) + ':')
    depth, i = 0, text.index('{', start)
    for end in range(i, len(text)):
        depth += {'{': 1, '}': -1}.get(text[end], 0)
        if depth == 0:
            break
    block = text[i:end + 1]
    for key, value in changes.items():
        found = re.findall(r'("' + re.escape(key) + r'"\s*:\s*)([^,\n}]+)', block)
        if len(found) != 1:
            raise SystemExit(f'ERROR: {queue}: {key} is set {len(found)} times at its top level, not once')
        block = re.sub(r'("' + re.escape(key) + r'"\s*:\s*)([^,\n}]+)',
                       lambda m: m.group(1) + json.dumps(value), block, count=1)
    return text[:i] + block + text[end + 1:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('action', choices=('show', 'set'))
    ap.add_argument('queue')
    ap.add_argument('settings', nargs='*')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    iri = Iri()
    before_stat = iri.stat(LIVE)
    text = iri.read(LIVE)
    config = json.loads(text)
    if args.queue not in config:
        raise SystemExit(f'ERROR: no queue {args.queue}; queues: {sorted(config)}')
    queue = config[args.queue]
    if args.action == 'show':
        print(json.dumps(queue, indent=1))
        return
    changes = {}
    for item in args.settings:
        key, value = item.split('=', 1)
        changes[key] = json.loads(value)
    print(json.dumps({k: {'from': queue.get(k), 'to': v} for k, v in changes.items()}))
    if not args.apply:
        return
    new_text = edit_text(text, args.queue, changes)
    expected = json.loads(text)
    expected[args.queue].update(changes)
    if json.loads(new_text) != expected:
        raise SystemExit('ERROR: the edit changes more than the settings named; nothing written')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if iri.stat(LIVE) != before_stat or iri.read(LIVE) != text:
        raise SystemExit('ERROR: the live file changed since it was read; nothing written')
    backup, side = f'{LIVE}-backup-{stamp}', f'{LIVE}.upload-{stamp}'
    iri.copy(LIVE, backup)
    if iri.read(backup) != text:
        raise SystemExit(f'ERROR: backup {backup} does not match the live file; nothing else written')
    iri.upload(side, new_text)
    if iri.read(side) != new_text:
        raise SystemExit(f'ERROR: the uploaded {side} does not match the edit; live file untouched')
    try:
        iri.copy(side, LIVE)
    except SystemExit as e:
        # The API's cp preserves times, which only the file's owner may set;
        # the content is written first. The read-back below decides.
        if 'preserving times' not in str(e):
            raise
    iri.remove(side)
    after = json.loads(iri.read(LIVE))
    after_stat = iri.stat(LIVE)
    if any(after[args.queue].get(k) != v for k, v in changes.items()):
        raise SystemExit(f'ERROR: the live file does not read the edit; restore from {backup}')
    print(json.dumps({'backup': backup, 'queue': args.queue, 'now': {k: after[args.queue].get(k) for k in changes},
                      'owner_mode_before': [before_stat.get(k) for k in ('uid', 'gid', 'mode')],
                      'owner_mode_after': [after_stat.get(k) for k in ('uid', 'gid', 'mode')]}))


if __name__ == '__main__':
    sys.exit(main())

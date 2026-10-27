import hashlib, json, os, sys
SP = '/opt/panda/lib/python3.11/site-packages'
out = {}
for pkg in ('pandaserver', 'pandajedi'):
    for root, _, files in os.walk(os.path.join(SP, pkg)):
        if '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.pyc'):
                continue
            p = os.path.join(root, f)
            data = open(p, 'rb').read()
            out[os.path.relpath(p, SP)] = hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
direct = open(next(os.path.join(SP, d, 'direct_url.json') for d in os.listdir(SP)
                   if d.startswith('panda_server-') and d.endswith('.dist-info'))).read()
json.dump({'direct_url': json.loads(direct), 'files': out}, sys.stdout)

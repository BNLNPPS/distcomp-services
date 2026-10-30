import hashlib, json, os, sys
# Run on osgsub01 or pandaharvester01 with Harvester's Python; compare with panda-server/audit/compare.py.
SP = '/opt/harvester/lib/python3.11/site-packages'
PACKAGES = ['pandaharvester']
out = {}
for pkg in PACKAGES:
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
                   if d.startswith('pandaharvester-') and d.endswith('.dist-info'))).read()
json.dump({'direct_url': json.loads(direct), 'packages': PACKAGES, 'files': out}, sys.stdout)

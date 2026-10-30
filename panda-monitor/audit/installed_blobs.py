import hashlib, json, os, sys
# Run on pandamon01 (no sudo needed); compare with nearest_commit.py.
ROOT = '/data/bigmon/core'
out, links = {}, {}
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for name in dirs + files:
        p = os.path.join(root, name)
        if os.path.islink(p):
            links[os.path.relpath(p, ROOT)] = os.readlink(p)
    for f in files:
        p = os.path.join(root, f)
        if f.endswith('.pyc') or os.path.islink(p):
            continue
        data = open(p, 'rb').read()
        out[os.path.relpath(p, ROOT)] = hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
json.dump({'root': ROOT, 'files': out, 'links': links}, sys.stdout)

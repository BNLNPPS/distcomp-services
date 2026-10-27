#!/usr/bin/env python3
"""Prepare a local patch from the installed files (UPGRADE.md, Local changes on
the host).

    prepare.py <patch dir holding edits.json> --source <installed files, site-packages layout> --output <dir>

edits.json names the patch, its exact replacements per file and the services to
restart. Each replacement must match exactly once in the installed file, and the
result must parse, or nothing is written. Writes the patched files under
<output>/files/, <output>/<name>.patch, <output>/manifest.json (each file's
SHA-256 before and after) and a copy of edits.json. host-install.py installs.
"""
import argparse
import ast
import difflib
import hashlib
import json
import shutil
from pathlib import Path


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('patch', type=Path)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    spec = json.loads((args.patch / 'edits.json').read_text())
    patched, diff, files = {}, [], {}
    for name, edits in spec['edits'].items():
        original = (args.source / name).read_text()
        text = original
        for old, new in edits:
            if text.count(old) != 1:
                raise SystemExit(f'ERROR: {name}: a replacement matches {text.count(old)} times, not once')
            text = text.replace(old, new)
        ast.parse(text)
        patched[name] = text
        diff += difflib.unified_diff(original.splitlines(True), text.splitlines(True), fromfile='a/' + name, tofile='b/' + name)
        files[name] = {'before_sha256': sha256(original), 'after_sha256': sha256(text)}
    for name, text in patched.items():
        target = args.output / 'files' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    (args.output / f"{spec['name']}.patch").write_text(''.join(diff))
    manifest = {'patch': spec['name'], 'restart': spec.get('restart', []), 'files': files}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    shutil.copy(args.patch / 'edits.json', args.output / 'edits.json')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()

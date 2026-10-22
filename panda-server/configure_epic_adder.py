#!/usr/bin/env python3
"""Select the separately installed ePIC adder; preserve every other setting."""
import argparse
import os
from pathlib import Path
import shutil
from datetime import datetime, timezone

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("path", type=Path)
args = parser.parse_args()
path = args.path.resolve()
source = path.read_text()
lines = source.splitlines(keepends=True)
matches = [i for i, line in enumerate(lines)
           if line.strip().startswith("adder_plugins =")]
if len(matches) != 1:
    raise SystemExit("Refused: expected exactly one active adder_plugins setting")
index = matches[0]
old = "dataservice.adder_simple_plugin:AdderSimplePlugin"
new = "swf_epicprod.panda.EpicAdderPlugin:EpicAdderPlugin"
entries = lines[index].split("=", 1)[1].strip().split(",")
for vo in ("wlcg", "epic"):
    matches = [i for i, entry in enumerate(entries) if entry.startswith(vo + ":")]
    if len(matches) != 1 or entries[matches[0]] not in (vo + ":" + old, vo + ":" + new):
        raise SystemExit(f"Refused: unexpected {vo} adder configuration")
    entries[matches[0]] = vo + ":" + new
lines[index] = "adder_plugins = " + ",".join(entries) + "\n"
updated = "".join(lines)
if source != updated:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(path.name + ".before-epic-adder-" + stamp)
    shutil.copy2(path, backup)
    temp = path.with_name(path.name + ".epic-adder-pending")
    # Create with the configuration's permissions before writing credentials.
    stat = path.stat()
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, stat.st_mode & 0o777)
    with os.fdopen(fd, "w") as stream:
        stream.write(updated)
        stream.flush()
        os.fsync(stream.fileno())
    shutil.copystat(path, temp)
    os.chown(temp, stat.st_uid, stat.st_gid)
    os.replace(temp, path)
    print("Backup:", backup)
print(lines[index].rstrip())

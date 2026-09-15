"""Load, under the gate venv, every class and module the ePIC configuration names.

Reads the modConfig lines of panda_jedi.cfg, the daemon config of
panda_server.cfg and the adder/setupper plugin lines, and imports each
target the way JEDI's FactoryBase, the daemon master and the plugin
loaders do. Reports what fails to import or lacks the named class.
Extra modules (e.g. the ePIC throttler) are given on the command line as
module:Class.
"""
import importlib
import json
import re
import sys

jedi_cfg, server_cfg = sys.argv[1], sys.argv[2]
extras = sys.argv[3:]
results = []


def check(kind, module, cls=None):
    try:
        m = importlib.import_module(module)
        if cls and not hasattr(m, cls):
            results.append((kind, f"{module}:{cls}", "FAIL", f"no class {cls}"))
        else:
            results.append((kind, f"{module}:{cls or ''}", "ok", ""))
    except BaseException as e:  # noqa: BLE001
        results.append((kind, f"{module}:{cls or ''}", "FAIL", f"{e.__class__.__name__}: {str(e).splitlines()[0][:160]}"))


# JEDI modConfig: vo:label:module:Class[:subtype]
for line in open(jedi_cfg):
    if line.startswith("modConfig"):
        for item in line.split("=", 1)[1].split(","):
            parts = item.strip().split(":")
            if len(parts) >= 4:
                check("jedi", parts[2], parts[3])

# daemon config: JSON block after "config =" in [daemon]
text = open(server_cfg).read()
sec = text.split("[daemon]", 1)[1].split("\n[", 1)[0]
package = re.search(r"^package\s*=\s*(\S+)", sec, re.M).group(1)
blob = sec.split("config", 1)[1].split("=", 1)[1]
cfg = json.loads(blob.strip())
for name, spec in cfg.items():
    if spec.get("enable"):
        check("daemon", f"{package}.{spec.get('module', name)}")

# plugins: vo:module:Class under pandaserver
for key in ("adder_plugins", "setupper_plugins", "closer_plugins"):
    m = re.search(rf"^{key}\s*=\s*(.+)$", text, re.M)
    if m:
        for item in m.group(1).split(","):
            parts = item.strip().split(":")
            if len(parts) == 3:
                check(key, "pandaserver." + parts[1], parts[2])

for e in extras:
    mod, _, cls = e.partition(":")
    check("extra", mod, cls or None)

fails = [r for r in results if r[2] == "FAIL"]
print(f"{len(results)} targets, {len(fails)} failed")
for r in results:
    print(f"{r[2]:4} {r[0]:16} {r[1]} {r[3]}")

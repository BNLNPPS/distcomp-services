import importlib, pkgutil, sys, traceback
SKIP = ("pandaserver.test.", "pandajedi.jeditest.", ".tests.", "pandaserver.daemons.master", "pandajedi.jediorder.JediMaster")
ok=[]; fail=[]
for pkg in ("pandaserver","pandajedi","pandacommon"):
    m=importlib.import_module(pkg)
    for info in pkgutil.walk_packages(m.__path__, pkg+"."):
        name=info.name
        if any(s in name for s in SKIP) or name.endswith(".test") or name.endswith(".jeditest") or name.endswith(".tests"):
            continue
        try:
            importlib.import_module(name); ok.append(name)
        except BaseException as e:
            fail.append((name, e.__class__.__name__, str(e).splitlines()[0][:200] if str(e) else ""))
print(f"imported {len(ok)} modules, {len(fail)} failed")
for n,c,msg in fail: print(f"FAIL {n}: {c}: {msg}")

# pandaharvester01 changes

Newest first. `pandaharvester01.sdcc.bnl.gov` runs the Harvester that submits the pull pilots of the GREX, JLab and Compute Canada queues (swf-epicprod `docs/SCHEDCONFIG_OVERRIDES.md`, `docs/COMPUTE_CANADA.md`). Reached from swf-testbed through the SCDF gateway like pandaserver01. Every change to Harvester's code goes upstream to HSF/harvester as a pull request (Torre Wenaus, 2026-10-29).

## Local changes on the host

Installed Harvester 0.7.6 from HSF/harvester commit `772f1579` (the merge of HSF/harvester#316, 2026-09-21), under `/opt/harvester/lib/python3.11/site-packages/pandaharvester/`, on 2026-10-08 by its file times; the previous installation is `/opt/harvester-backup-2026-10-08`. The comparison of the installed package with that commit uses the osgsub01 audit unchanged, the installation path being the same:

```
ssh ... "ssh pandaharvester01 'sudo -n /opt/harvester/bin/python -I -'" < ../osg-harvester/audit/installed_blobs.py > /tmp/installed.json
python3 ../panda-server/audit/compare.py /tmp/installed.json <harvester checkout>
```

No code change is installed here, so none is outstanding upstream. The comparison must find no installed file that differs from the commit. The only files not in the commit are two editor copies from 2024-07-04, carried forward through upgrades and never imported: `harvesterbody/master.py~` and `harvestercore/core_utils.py~`.

## 2026-10-30: installed package compared with its commit

- **By:** Claude swf-1, read only.
- **Result:** 253 installed files; none differs from commit `772f1579`, none of the commit is absent; the two editor copies above are the only extra files.

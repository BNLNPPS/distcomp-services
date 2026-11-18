# pandaharvester01 changes

Newest first. `pandaharvester01.sdcc.bnl.gov` runs the Harvester that submits the pull pilots of the GREX, JLab and Compute Canada queues (swf-epicprod `docs/SCHEDCONFIG_OVERRIDES.md`, `docs/COMPUTE_CANADA.md`). Reached from swf-testbed through the SCDF gateway like pandaserver01. Every change to Harvester's code goes upstream to HSF/harvester as a pull request (Torre Wenaus, 2026-10-29).

## Local changes on the host

Installed Harvester 0.7.6 from HSF/harvester commit `772f1579` (the merge of HSF/harvester#316, 2026-09-21), under `/opt/harvester/lib/python3.11/site-packages/pandaharvester/`, on 2026-10-08 by its file times; the previous installation is `/opt/harvester-backup-2026-10-08`. The comparison of the installed package with that commit uses the osgsub01 audit unchanged, the installation path being the same:

```
ssh ... "ssh pandaharvester01 'sudo -n /opt/harvester/bin/python -I -'" < ../osg-harvester/audit/installed_blobs.py > /tmp/installed.json
python3 ../panda-server/audit/compare.py /tmp/installed.json <harvester checkout>
```

No code change is installed here, so none is outstanding upstream. The comparison must find no installed file that differs from the commit. The only files not in the commit are two editor copies from 2024-07-04, carried forward through upgrades and never imported: `harvesterbody/master.py~` and `harvestercore/core_utils.py~`.

## 2026-11-17: JLAB_PanDA_1 back online for the retest JLab asked for

- **By:** Claude swf-9, for Torre Wenaus (his word of 2026-11-17: "try again as she asks").
- **Why:** JLab opened the farm's route to `pandaserver01.sdcc.bnl.gov:25443` and asked for a retry (Kathryn Strosahl, 2026-11-17 14:39 ET: "The network change seems to be going through, please try your workflow again"). The queue had been offline since the pause of 2026-10-22, when the farm could not reach the server.
- **What:** `JLAB_PanDA_1` `queueStatus` `offline` → `online` in `/opt/harvester/etc/panda/panda_queueconfig.json` at 21:52 ET; nothing else changed. Harvester rereads the file within its update interval. A landing probe followed: task 42024, `group.EIC.canary.jlab_panda_1.20261117215310`.
- **Rollback:** `panda_queueconfig.json.before-jlab-retest-20261118T025244Z` beside it.

## 2026-11-16: GREX submit template on the short-metric-names pilot runtime

- **By:** Claude swf-1, for Torre Wenaus (hilog work, his go of 2026-11-16).
- **What:** `/data/atlpan/harvester_common/submit_pilot3_pull_umgrex.sdf` now names runtime `native-grex-shortnames-fabf634` (its asset paths and `+EpicprodNative` only) at 20:58 ET, by swf-epicprod `scripts/retarget-native-grex.py`. The runtime's pilot archive writes its job metrics under short names so the payload's digest fits PanDA's 500 characters. No Harvester code or configuration changed; workers already submitted kept their runtime.
- **Verified:** payload canary task 42002 / job 6608500 on a new-runtime allocation, healthy, its metrics 381 characters with every field (swf-epicprod `docs/NATIVE_PILOT_CANARY.md`, Short metric names).
- **Rollback:** the previous template is beside it as `submit_pilot3_pull_umgrex.sdf.before-shortnames-20261117T015813Z` (runtime `native-grex-nosampler-a70e9dd`, still in place).

## 2026-10-30: installed package compared with its commit

- **By:** Claude swf-1, read only.
- **Result:** 253 installed files; none differs from commit `772f1579`, none of the commit is absent; the two editor copies above are the only extra files.

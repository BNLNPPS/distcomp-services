# pandaharvester01 changes

Newest first. `pandaharvester01.sdcc.bnl.gov` runs the Harvester that submits the pull pilots of the GREX, JLab and Compute Canada queues (swf-epicprod `docs/SCHEDCONFIG_OVERRIDES.md`, `docs/COMPUTE_CANADA.md`). Reached from swf-testbed through the SCDF gateway like pandaserver01. Every change to Harvester's code goes upstream to HSF/harvester as a pull request (Torre Wenaus, 2026-10-29).

## Local changes on the host

Installed Harvester 0.7.6 from HSF/harvester commit `772f1579` (the merge of HSF/harvester#316, 2026-09-21), under `/opt/harvester/lib/python3.11/site-packages/pandaharvester/`, on 2026-10-08 by its file times; the previous installation is `/opt/harvester-backup-2026-10-08`. The comparison of the installed package with that commit uses the osgsub01 audit unchanged, the installation path being the same:

```
ssh ... "ssh pandaharvester01 'sudo -n /opt/harvester/bin/python -I -'" < ../osg-harvester/audit/installed_blobs.py > /tmp/installed.json
python3 ../panda-server/audit/compare.py /tmp/installed.json <harvester checkout>
```

No code change is installed here, so none is outstanding upstream. The comparison must find no installed file that differs from the commit. The only files not in the commit are two editor copies from 2024-07-04, carried forward through upgrades and never imported: `harvesterbody/master.py~` and `harvestercore/core_utils.py~`.

## 2026-11-18: GREX and JLab on runtime native-grex-pidsearch-e2ee25c

- **By:** Claude swf-1, for Torre Wenaus (his approval of the rollout and its canaries, 2026-11-18).
- **Why:** the direct pilot held a payload that ends within a fraction of a second for ten minutes on GREX and JLab: the memory monitor's payload search ran its 120 five-second tries on an exited, unreaped payload (swf-epicprod `docs/NATIVE_PILOT_CANARY.md`, The memory monitor's payload search).
- **What:** runtime `/data/atlpan/harvester_common/native-grex-pidsearch-e2ee25c`, staged by swf-epicprod `scripts/stage-native-runtime.py` at commit `e2ee25c`; pilot archive SHA-256 `61fb982a7855c806592e49bf86e4288177d16f2716f85b37483a0c2e3378a7c3`, built by `pilot/native-canary/build.py --production --heartbeat-seconds 300` from the epic5 baseline. It differs from the previous runtime only in the archive, and the archive from `aad45ad9` only in `utilities.py`, `common.py`, `native_container.py` and an unused helper in `metric_keys.py`. At 22:07:49 ET `submit_pilot3_pull_umgrex.sdf` retargeted by `scripts/retarget-native-grex.py` (SHA-256 `eeaa0f0ea78affc18d0952fa426145a965166fc9c43948c80525b87a8960214a`); at 22:08:08 ET `submit_pilot3_pull_jlab.sdf` re-rendered by `scripts/render-native-jlab.py --max-memory 6000` (SHA-256 `75fd227c4cccfccc20880f4697cbcf97aaefeb727180cebe71ce735dda504f83`). Only asset paths and `+EpicprodNative` changed. Workers already submitted keep their runtime. `panda_queueconfig.json` `executableFile` still names the previous runtime's launcher, which remains in place.
- **Verified:** on new-runtime pilots the instant-payload probe finished in 7 s on GREX (job 6609580) and 6 s on JLab (job 6609581), against ten minutes before; payload canaries 6609578 (GREX) and 6609579 (JLab) finished with 100 events each.
- **Rollback:** `submit_pilot3_pull_umgrex.sdf.before-pidsearch-20261119T030749Z` and `submit_pilot3_pull_jlab.sdf.before-pidsearch-20261119T030808Z` beside the live templates.

## 2026-11-17: JLAB_PanDA_1 pilots request 6,000 MB

- **By:** Claude swf-9, for Torre Wenaus (his go for the JLab trial, 2026-11-17).
- **Why:** the pilot asked JLab's Slurm for 2,000 MB while the queue record's `maxrss` is 6,000 MB (swf-epicprod `docs/SCHEDCONFIG_OVERRIDES.md`), so PanDA could hand a pilot a production job larger than its allocation.
- **What:** at 22:44 ET `submit_pilot3_pull_jlab.sdf` re-rendered with `scripts/render-native-jlab.py --max-memory 6000`; only `+maxMemory` changed. SHA-256 `776148373a45137ef946cda52817ed76ec509dc5f0dce78eb63ddc0102d37307`.
- **Rollback:** `submit_pilot3_pull_jlab.sdf.before-6000mb-20261118T034407Z`.

## 2026-11-17: executableFile names the direct-pilot launcher

- **By:** Claude swf-9, for Torre Wenaus (2026-11-17, "change them").
- **What:** at 22:38 ET `UM_GREX_PanDA_1` and `JLAB_PanDA_1` in `panda_queueconfig.json` name their template's launcher, `native-grex-shortnames-fabf634/epicprod-multipilot.sh`, as `executableFile` in place of `bnlpanda.runpilot2-wrapper.sh`. The templates' own `executable` lines already overrode it, so submission is unchanged; the entries no longer name the obsolete retired pilot. A runtime retarget of the template leaves this value naming the previous asset directory until it is set again.
- **Rollback:** `panda_queueconfig.json.before-exe-direct-20261118T033841Z`.

## 2026-11-17: JLAB_PanDA_1 on the direct pilot

- **By:** Claude swf-9, for Torre Wenaus (2026-11-17: "THE DIRECT PILOT IS SUPPOSED TO BE FREE OF ATLAS SW DEPENDENCIES"; "WE NEVER EVER EVER USE THE STOCK PILOT AGAIN").
- **Why:** the retest's canary job 6608533 reached the server, then failed in one second (pilot 1186, then 1310): JLab's launcher `jlab-native-pilot.sh` ran the obsolete retired pilot through `bnlpanda.runpilot2-wrapper.sh`, whose container setup requires `/cvmfs/atlas.cern.ch`, absent on the JLab farm.
- **What:** at 22:28 ET `/data/atlpan/harvester_common/submit_pilot3_pull_jlab.sdf` is rendered by swf-epicprod `scripts/render-native-jlab.py` from GREX's live template: GREX's direct-pilot runtime `native-grex-shortnames-fabf634` (launcher, archive, helpers, environment, pilot arguments) with one pilot per batch job (`EPICPROD_PILOTS_PER_SLOT=1`, `EPICPROD_ALLOCATION_SECONDS=86400`); JLab's CE, SciTokens authentication with the proxy as an ordinary input, one core, `maxMemory`, `maxWallTime` 1440 and queue data kept. SHA-256 `7c85c4754c96ddc3dc54d800fd42637e302f13ecc285e1627957851da1e9afc2`. The JLab pilots of the old template had all completed.
- **Rollback:** `submit_pilot3_pull_jlab.sdf.before-native-20261118T032856Z` beside it.

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

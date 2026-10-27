#!/usr/bin/env python3
"""Prepare the fine-grained range-size patch from the installed files.

Fine-grained Event Service tasks get ranges of nEventsPerFineGrainedRange
events (split rule FR) instead of JEDI's single-event ranges; a task without
the parameter is unchanged. The same change is the upstream pull request on
PanDAWMS/panda-server (branch fine-grained-range-size).

    prepare.py --source <dir holding the installed files, site-packages layout> --output <dir>

Writes the patched files under <output>/files/, the unified diff
<output>/fine-grained-range-size.patch and <output>/manifest.json with each
file's SHA-256 before and after. Every replacement must match exactly once in
the installed file, or nothing is written. Installation is host-install.py.
"""
import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path

EDITS = {
    'pandaserver/taskbuffer/task_split_rules.py': [(
        '    "fineGrainedProc": "FP",\n',
        '    "fineGrainedProc": "FP",\n    "nEventsPerFineGrainedRange": "FR",\n',
    )],
    'pandaserver/taskbuffer/JediTaskSpec.py': [(
        '''    def is_fine_grained_process(self) -> bool:
        return self.check_split_rule("fineGrainedProc")
''',
        '''    def is_fine_grained_process(self) -> bool:
        return self.check_split_rule("fineGrainedProc")

    # get the number of events per event range for fine-grained processing
    def get_fine_grained_range_size(self) -> int:
        if self.splitRule is not None:
            tmpMatch = re.search(r"(?:^|,)" + self.splitRuleToken["nEventsPerFineGrainedRange"] + r"=(\\d+)", self.splitRule)
            if tmpMatch is not None and int(tmpMatch.group(1)) > 0:
                return int(tmpMatch.group(1))
        return 1
''',
    )],
    'pandajedi/jedirefine/TaskRefinerBase.py': [(
        '''        if "fineGrainedProc" in taskParamMap and taskParamMap["fineGrainedProc"]:
            self.setSplitRule(None, 1, JediTaskSpec.splitRuleToken["fineGrainedProc"])
''',
        '''        if "fineGrainedProc" in taskParamMap and taskParamMap["fineGrainedProc"]:
            self.setSplitRule(None, 1, JediTaskSpec.splitRuleToken["fineGrainedProc"])
            # events per range, one by default
            if taskParamMap.get("nEventsPerFineGrainedRange"):
                self.setSplitRule(taskParamMap, "nEventsPerFineGrainedRange", JediTaskSpec.splitRuleToken["nEventsPerFineGrainedRange"])
''',
    )],
    'pandajedi/jediorder/JobGenerator.py': [(
        '''                                    elif taskSpec.is_fine_grained_process():
                                        nEventsPerWorker = 1
''',
        '''                                    elif taskSpec.is_fine_grained_process():
                                        nEventsPerWorker = taskSpec.get_fine_grained_range_size()
''',
    )],
    'pandaserver/taskbuffer/db_proxy_mods/task_event_module.py': [(
        '''                                    tmpM = re.search("ES=(\\d+)", splitRule)
                                    if tmpM is not None:
                                        nEventsDef = int(tmpM.group(1))
''',
        '''                                    tmpM = re.search("ES=(\\d+)", splitRule)
                                    if tmpM is not None:
                                        nEventsDef = int(tmpM.group(1))
                                    else:
                                        # events per range of fine-grained processing
                                        tmpM = re.search(
                                            r"(?:^|,)" + JediTaskSpec.splitRuleToken["nEventsPerFineGrainedRange"] + r"=(\\d+)",
                                            splitRule,
                                        )
                                        if tmpM is not None:
                                            nEventsDef = int(tmpM.group(1))
''',
    )],
}


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    patched, diff, manifest = {}, [], {'patch': 'fine-grained-range-size', 'files': {}}
    for name, edits in EDITS.items():
        original = (args.source / name).read_text()
        text = original
        for old, new in edits:
            if text.count(old) != 1:
                raise SystemExit(f'ERROR: {name}: the replacement matches {text.count(old)} times, not once')
            text = text.replace(old, new)
        ast.parse(text)
        patched[name] = text
        diff += difflib.unified_diff(original.splitlines(True), text.splitlines(True),
                                     fromfile='a/' + name, tofile='b/' + name)
        manifest['files'][name] = {'before_sha256': sha256(original), 'after_sha256': sha256(text)}
    for name, text in patched.items():
        target = args.output / 'files' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    (args.output / 'fine-grained-range-size.patch').write_text(''.join(diff))
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()

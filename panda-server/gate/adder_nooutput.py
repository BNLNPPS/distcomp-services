#!/usr/bin/env python3
"""Check the installed ePIC adder with real PanDA classes and mocked Rucio.

Run as atlpan with /opt/panda/bin/python after installing swf-epicprod,
before restarting panda_daemon. No catalog or database writes are made.
"""
import logging
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pandaserver.dataservice import adder_simple_plugin
from pandaserver.taskbuffer.FileSpec import FileSpec
from pandaserver.taskbuffer.JobSpec import JobSpec
from swf_epicprod.panda.EpicAdderPlugin import EpicAdderPlugin


for states in [("nooutput",), ("failed",), ("ready",),
               ("nooutput", "failed", "ready")]:
    job = JobSpec()
    job.computingSite = "BNL_OSG_PanDA_1"
    for i, state in enumerate(states):
        file = FileSpec()
        file.type = "log"
        file.status = state
        file.destinationSE = "BNL-XRD"
        file.fsize = 123 if state == "ready" else 0
        file.lfn = f"log-{i}.tgz"
        file.checksum = "ad:00000001"
        file.destinationDBlock = "logs"
        job.addFile(file)
    files = job.Files
    mapper = Mock()
    mapper.getSite.return_value = SimpleNamespace(ddm_output={"default": "BNL-XRD"})
    plugin = EpicAdderPlugin(job, siteMapper=mapper, logger=logging.getLogger("gate"))
    with patch.object(adder_simple_plugin, "rucioAPI") as api:
        plugin.execute()
        assert plugin.result.is_succeeded(), states
        assert job.Files is files, "original file records were not restored"
        expected = [f.lfn for f in files if f.status == "ready"]
        if expected:
            api.register_files_in_dataset.assert_called_once()
            actual = api.register_files_in_dataset.call_args.args[0]["BNL-XRD"]["logs"]
            assert [f["lfn"] for f in actual] == expected, (states, actual)
        else:
            api.register_files_in_dataset.assert_not_called()
print("PASS: actual PanDA JobSpec and FileSpec; absent/failed files skipped; present log registered; all records restored")

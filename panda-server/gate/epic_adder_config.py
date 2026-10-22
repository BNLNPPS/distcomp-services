#!/usr/bin/env python3
"""Require the actual adder entry point to load both configured ePIC plugins."""
from pandaserver.dataservice import adder_gen  # noqa: F401; loads plugin configuration
from pandaserver.config import panda_config

for vo in ("wlcg", "epic"):
    plugin = panda_config.getPlugin("adder_plugins", vo)
    assert plugin is not None, f"No adder for {vo}"
    assert plugin.__module__ == "swf_epicprod.panda.EpicAdderPlugin", (vo, plugin)
    assert plugin.__name__ == "EpicAdderPlugin", (vo, plugin)
    print(vo, plugin.__module__ + "." + plugin.__name__)

#!/usr/bin/python
# picons-missing.py - Version for UTF8 SNP picons only
# mod by lululla

import os
import json

from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox


def main(session, **kwargs):
    # Get picon locations
    try:
        from Components.Renderer.Picon import piconLocator
        piconLocations = piconLocator.searchPaths
    except:
        try:  # openatv are using a global
            from Components.Renderer.Picon import searchPaths
            piconLocations = searchPaths
        except:
            piconLocations = ""

    if piconLocations:
        piconLocations = list(map(lambda x: os.path.join(x, ""), piconLocations))

        # Create choice menu
        menu = [
            ("Search for UTF8 SNP picons only (NEW)", "utf8snp"),
            ("Search for all picon formats (original)", "all"),
            ("Cancel", "cancel")
        ]

        session.openWithCallback(
            lambda result: runPiconSearch(session, piconLocations, result),
            ChoiceBox,
            title="Select picon search mode:",
            list=menu
        )
    else:
        session.open(MessageBox, "No picon locations found!", MessageBox.TYPE_ERROR)


def runPiconSearch(session, piconLocations, result):
    if result is None or result[1] == "cancel":
        return

    plugin_dir = os.path.dirname(os.path.realpath(__file__))

    if result[1] == "utf8snp":
        title = "Picons Missing (UTF8 SNP only)"
        script = os.path.join(plugin_dir, "missingPiconsUTF8SNP.py")
        command = "python %s '%s'" % (script, json.dumps(piconLocations))
    else:  # "all" - original behavior
        title = "Picons Missing (All formats)"
        script = os.path.join(plugin_dir, "picons-missing.py")
        command = "python %s '%s' 1" % (script, json.dumps(piconLocations))

    session.open(Console, title=title, cmdlist=[command])


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name='Picons Missing',
            description='Creates a list of missing picons in /tmp directory',
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main,
            icon='plugin.png')]

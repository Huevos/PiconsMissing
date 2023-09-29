import os
import json

from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console

def main(session, **kwargs):
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
		piconLocations = list(map(lambda x: os.path.join(x, ""), piconLocations))  # ensure trailing slash
	script = os.path.join(os.path.dirname(os.path.realpath(__file__)), "picons-missing.py")
	command = "python %s '%s' 1" % (script, json.dumps(piconLocations))
	session.open(Console, title='Picons Missing', cmdlist=[command])


def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name='Picons Missing', 
			description='Creates a list of missing picons in /tmp directory', 
			where=PluginDescriptor.WHERE_PLUGINMENU, 
			fnc=main, 
			icon='plugin.png')]

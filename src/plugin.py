from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console

def main(session, **kwargs):
	session.open(Console, title='Picons Missing', cmdlist=['python /usr/lib/enigma2/python/Plugins/Extensions/PiconsMissing/picons-missing.py 1'])


def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name='Picons Missing', 
			description='Creates a list of missing picons in /tmp directory', 
			where=PluginDescriptor.WHERE_PLUGINMENU, 
			fnc=main, 
			icon='plugin.png')]

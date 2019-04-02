# init work
import sys
import os
from patterncoding.myTemplateEngine import MyTemplateEngine
from appPublic.jsonConfig import getConfig
from WebServer.webUtils import getClientType
from appPublic.Singleton import GlobalEnv
from WebServer.globalEnv import globalFunctions

from appPublic.MiniI18N import getI18N
def setupTemplateEngines():
	conf = getConfig()
	clientAdapter = conf.website.clientAdapter
	for k,v in clientAdapter.items():
		v = getattr(conf.website.clientAdapter,k)
		v.myTemplateEngine = MyTemplateEngine(v.tmplpath,conf.template_file_coding,conf.website.coding)

def getTemplateEngine(request):
	config = getConfig()
	client = getClientType(request)
	adapter = config.website.clientAdapter.get(client,config.website.clientAdapter.get("default"))
	te = adapter.myTemplateEngine
	return te

def myTemplateEngine(request):
	config = getConfig()
	client = getClientType(request)
	v  = config.website.clientAdapter.get(client,'default')
	te = MyTemplateEngine(v.tmplpath,config.template_file_coding,config.website.coding)
	ge = GlobalEnv()
	te.env.globals.update(ge)
	return te
	
def initWorks(workdir):
	ge = GlobalEnv()
	for k,v in globalFunctions.items():
		ge[k] = v
	sys.path.append(os.path.join(workdir,'plugins'))
	try:
		import globalPlugin as gp
		pg.l=plugin()
	except:
		pass
		
	config = getConfig()
	config.i18n = getI18N()
	ge['coding'] = config.website.coding
	ge['databases'] = config.databases
	

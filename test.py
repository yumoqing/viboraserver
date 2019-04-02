import sys
import os
import logging

from patterncoding.myTemplateEngine import MyTemplateEngine

from appPublic.folderUtils import ProgramPath
from appPublic.jsonConfig import getConfig

from sql.sqlorAPI import DBPools

from viboraserver.acBase import BaseResource
from viboraserver.serverenv import ServerEnv

from vibora import Vibora

def setupEnv():
	env = ServerEnv()
	config = getConfig()
	env.int = int
	env.float = float
	env.tmplRender = MyTemplateEngine([],
				config.website.coding,
				config.website.coding)
	env.tmplRender.env.globals.update(env)

def start():
	workdir = programPath = ProgramPath()
	if len(sys.argv)>1:
		workdir = sys.argv[1]
	config = getConfig(workdir,{'ProgramPath':programPath,'workdir':workdir})
	setupEnv()
	DBPools(config.databases)
	resource = BaseResource(paths=config.website.paths)
	resource.indexes = config.website.indexes
	resource.processors = config.website.processors
	print(resource.indexes)
	app = Vibora( static = resource)
	app.run(debug=config.debug,host=config.website.host,port=config.website.port)

if __name__ == '__main__':
	start()

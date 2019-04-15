import sys
import os
import logging

from patterncoding.myTemplateEngine import MyTemplateEngine

from appPublic.folderUtils import ProgramPath
from appPublic.jsonConfig import getConfig

from sql.sqlorAPI import DBPools

from viboraserver.acBase import MyApp, BaseResource
from viboraserver.serverenv import ServerEnv
from viboraserver.xlsxdsProcessor import XLSXDataSourceProcessor
from viboraserver.myTE import setupTemplateEngine

from vibora.request import Request
from vibora.responses import Response,CachedResponse

def start():
	workdir = programPath = ProgramPath()
	if len(sys.argv)>1:
		workdir = sys.argv[1]
	config = getConfig(workdir,{'ProgramPath':programPath,'workdir':workdir})
	DBPools(config.databases)
	resource = BaseResource(config.website.paths,indexes=config.website.indexes)
	setupTemplateEngine()
	resource.indexes = config.website.indexes
	resource.processors = config.website.processors
	print(resource.indexes)
	app = MyApp( static = resource)
	resource.app = app
	# the follow not work, Why?
	@app.route('/getI18nDict',methods=['POST','GET'])
	async def getI18nDict(request:Request):
		return CachedResponse('hello world')
	# above not work
	app.run(debug=config.debug,host=config.website.host,port=config.website.port)

if __name__ == '__main__':
	start()

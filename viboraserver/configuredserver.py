
import sys
import os
import logging

from appPublic.folderUtils import ProgramPath
from appPublic.jsonConfig import getConfig

from sqlor.dbpools import DBPools

from .globalEnv import initEnv
from .acBase import MyApp, BaseResource
from .serverenv import ServerEnv
from .xlsxdsProcessor import XLSXDataSourceProcessor
from .myTE import setupTemplateEngine
from .sslsock import openSslSock

from vibora.request import Request
from vibora.responses import Response,CachedResponse


class ConfiguredServer:
	def __init__(self):
		workdir = programPath = ProgramPath()
		if len(sys.argv)>1:
			workdir = sys.argv[1]
		config = getConfig(workdir,{'ProgramPath':programPath,'workdir':workdir})
		if config.get('databases'):
			DBPools(config.databases)
		initEnv()
		paths = [ os.path.abspath(p) for p in config.website.paths ]
		resource = BaseResource(paths,indexes=config.website.indexes)
		setupTemplateEngine()
		resource.indexes = config.website.indexes
		resource.processors = config.website.processors
		self.app = MyApp( static = resource)
		resource.app = self.app

	def run(self):
		config = getConfig()
		ssock = None
		host = config.website.get('host','0.0.0.0')
		port = config.website.get('port',8080)
		if config.website.get('ssl',False):
			ssock = openSslSock(
					host,
					port,
					config.website.ssl.crtfile,
					config.website.ssl.keyfile)
		self.app.run(debug=config.get('debug',True),
			host=host,
			port=port,
			sock=ssock)
		

if __name__ == '__main__':
	server = ConfiguredServer()
	server.run()

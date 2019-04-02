from twisted.web import static 
from twisted.web.server import Site
from twisted.internet import reactor,ssl
from twisted.internet import defer
defer.setDebugging(True)

from appPublic.jsonConfig import getConfig
from WebServer.acBase import BaseResource
from WebServer.configuredResource import I18nResource,BaseProcessor
from WebServer import dsProcessor
from WebServer import sqldsProcessor
from WebServer import xlsxdsProcessor
from WebServer import mdProcessor

def getProcessor(name):
	return _getProcessor(BaseProcessor,name)
	
def _getProcessor(kclass,name):
	for k in kclass.__subclasses__():
		if not hasattr(k,'isMe'):
			continue
		if k.isMe(name):
			return k
		a = _getProcessor(k,name)
		if a is not None:
			return a
	return None
	
def addProcessors(resource,processors):
	p = {}
	config = getConfig()
	for s,k in processors.items():
		klass = getProcessor(k)
		p[s] = klass
	resource.newProcessors = p
	
class EasyServer:
	def __init__(self,ac):
		self.conf = getConfig()
		self.licenseChecker = None
		self.root = BaseResource(self.conf.website.root,accessController=ac)
		self.limited = False
		self.serverObj = None
		self._reactor = reactor
		if self.conf.website.get('threads',False):
			self._reactor.suggestThreadPoolSize(self.conf.website.threads)
		else:
			self._reactor.suggestThreadPoolSize(200)
	
	def addChild(self,key,handler):
		self.root.putChild(key,handler)
		
	def setLimited(self):
		self.limited = True
	
	def setRoot(self,root):
		self.root = rootResource
	
	def getRoot(self):
		return self.root
		
	def stop(self):
		self._reactor.stop()
		
	def restart(self):
		self.stop()
		self.start()
	def setServerStuff(self):
		i18nD = I18nResource()
		self.root.putChild(b'getI18nDict',i18nD)
		if isinstance(self.root,BaseResource):
			addProcessors(self.root,self.conf.website.processors)
			self.root.indexNames = self.conf.website.indexes
		else:
			print('is not a File resource')
		
	def start(self):
		self.setServerStuff()
		host = self.conf.website.host
		port = self.conf.website.port
		self.site = Site(self.root)
		if self.conf.website.get('ssl',False):
			# print(self.conf.website.ssl.keyfile,self.conf.website.ssl.crtfile)
			sslContext = ssl.DefaultOpenSSLContextFactory(
				self.conf.website.ssl.keyfile, # 私钥
				self.conf.website.ssl.crtfile # 证书
			)
			p1 = self._reactor.listenSSL(port,self.site,sslContext,interface=host)
		else:
			p1 = self._reactor.listenTCP(port, self.site,interface=host)
		p = p1.getHost()
		print("server running at:", p.host,p.port)
		if self.limited:
			self._reactor.suggestThreadPoolSize(1)
		self._reactor.run()
			
	def restart(self):
		pass
	

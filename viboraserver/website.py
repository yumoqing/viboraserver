# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
import sys
import time
from twisted.internet import reactor
from twisted.web import static
from twisted.web.resource import Resource
from twisted.internet import threads
from appPublic.jsonConfig import getConfig
from twisted.web import server, resource, guard
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from zope.interface import Interface, Attribute, implements
from twisted.python.components import registerAdapter
from twisted.web.server import Session
from twisted.web.script import ResourceScript
from twisted.cred import error
from twisted.web import util
from twisted.web._auth.wrapper import UnauthorizedResource
from twisted.web.resource import IResource, ErrorPage
from twisted.cred.credentials import Anonymous

from odbcUserCheck import ODBCUserChecker

from funcResource import FuncAsyncRequest,FuncRequest,FunctionList,missFunc

from pythonJson import PythonJson
from pageRenderer import PageRenderer
from initWork import initWorks

# from ds.dsengine import DSEngine

processors={
	'.rpy':ResourceScript,
	'.page':PageRenderer,
}
class IUser(Interface):
	id = Attribute("An string value which represent logioned user")
	
class User(object):
	implements(IUser)
	def __init__(self,session):
		self.id = None

registerAdapter(User,Session,IUser)
 
class SimpleRealm(object):
	"""
	A realm which gives out L{GuardedResource} instances for authenticated
	users.
	"""
	implements(IRealm)

	def __init__(self,rootObj):
		self.resource = rootObj
		
	def requestAvatar(self, avatarId, mind, *interfaces):
		if resource.IResource in interfaces:
			return resource.IResource, self.resource, lambda: None
		raise NotImplementedError()


class MyHTTPAuthSessionWrapper(guard.HTTPAuthSessionWrapper):
	def __init__(self,config):
		self.handler = None
		self.config = config
		self._makeup()
		checkers = [
			#InMemoryUsernamePasswordDatabaseDontUse(joe='blow',glue='glue',ymq='ymq123'),
			#ODBCUserChecker("DSN=pmdb1","select password from users where userid=?")
		]
		portal = Portal(SimpleRealm(self.root), checkers)
		guard.HTTPAuthSessionWrapper.__init__(self,portal,[guard.DigestCredentialFactory('md5', 'example.com')])

	def addChecker(self,checker):
		self.checkers.append(checker)
			
	def _authorizedResource(self, request):
		"""
		Get the L{IResource} which the given request is authorized to receive.
		If the proper authorization headers are present, the resource will be
		requested from the portal.  If not, an anonymous login attempt will be
		made.
		"""
				
		authheader = request.getHeader('authorization')

		if not authheader:
			return util.DeferredResource(self._login(Anonymous(),request))

		factory, respString = self._selectParseHeader(authheader)
		if factory is None:
			return UnauthorizedResource(self._credentialFactories)
		try:
			credentials = factory.decode(respString, request)
		except error.LoginFailed:
			return UnauthorizedResource(self._credentialFactories)
		except:
			log.err(None, "Unexpected failure from credentials factory")
			return ErrorPage(500, None, None)
		else:
			return util.DeferredResource(self._login(credentials,request))

	def _updateSession(self,user=None,req=None):
		session = req.getSession()
		session.userid = user.username
		userid = user.username
		u = IUser(session)
		u.id = userid
		
	def _login(self, credentials,request):
		"""
		Get the L{IResource} avatar for the given credentials.

		@return: A L{Deferred} which will be called back with an L{IResource}
			avatar or which will errback if authentication fails.
		"""

		d = self._portal.login(credentials, None, IResource)
		d.addCallbacks(self._loginSucceeded, self._loginFailed,callbackKeywords={'user':credentials,'req':request})
		return d

	def _loginSucceeded(self, args,user=None,req=None):
		authheader = req.getHeader('authorization')
		if authheader is None:
			self._updateSession(user,req)

		return guard.HTTPAuthSessionWrapper._loginSucceeded(self,args)
		
	def stop(self):
		self.handler.stopListening()
		
	def _makeup(self):
		self.root = static.File(self.config['root'])
		self.root.processors = processors

		for k,t,o in self.config['urls']:
			if t == 'S':
				self.addFilePath(k,o)
			elif t == 'F':
				obj = FunctionList.get(o,missFunc)
				self.addFuncPath(k,obj)
			elif t == 'f':
				obj = FunctionList.get(o,missFunc)
				self.addAsyncFuncPath(k,obj)
			else:
				print( "undefined node type:",t)
		self.site = server.Site(self)
					
	def start(self):
		print( "server waiting at ",self.config['port'])
		self.handler = reactor.listenTCP(self.config['port'], self.site)

	def addPath(self,path,obj):
		o = self.root
		keys = path.split('/')
		if len(keys) < 2:
			raise Exception("addFuncPath():path=" + path + " error")
		
		for p in path.split('/')[1:-1]:
			try:
				o = o.getChild(p)
			except:
				r = Resource()
				o.putChild(p,r)
				o = r
				
		o.putChild(keys[-1],obj)

	def addFuncPath(self,path,func):
		obj = FuncRequest(func)
		self.addPath(path,obj)
	
	def addAsyncFuncPath(self,path,func):
		obj = FuncAsyncRequest(func)
		self.addPath(path,obj)
	
	def addFilePath(self,path,filename):
		obj = static.File(filename)
		obj.processors = processors
		self.addPath(path,obj)
		
if __name__ == '__main__':
	def mytest(request):
		return "hello here"
		
	if len(sys.argv)>1:
		config = getConfig(sys.argv[1])
	else:
		config = getConfig()
	
	initWorks()
	website=config.website
	web = MyHTTPAuthSessionWrapper(website)
	web.addFuncPath('/mytest.html',mytest)
	web.start()
	reactor.run()
	# del config.engine
	print( "finish")

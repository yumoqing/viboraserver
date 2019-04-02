# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
import sys
import time

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.internet import threads
from appPublic.jsonConfig import getConfig
from twisted.web import server, resource, guard
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import ICredentialsChecker,InMemoryUsernamePasswordDatabaseDontUse
from zope.interface import Interface, Attribute, implements,implementer
from twisted.python.components import registerAdapter
from twisted.web.server import Session
from twisted.cred import error
from twisted.web import util
from twisted.web._auth.wrapper import UnauthorizedResource
from twisted.web.resource import IResource, ErrorPage
from twisted.cred.credentials import Anonymous,IUsernamePassword,IUsernameHashedPassword
from twisted.web.guard import HTTPAuthSessionWrapper, DigestCredentialFactory,BasicCredentialFactory
from appPublic.unicoding import unicoding
from twisted.internet import defer

from twisted.python.compat import networkString
def render(self, request):
	"""
	Send www-authenticate headers to the client
	"""
	def generateWWWAuthenticate(scheme, challenge):
		l = []
		for k,v in challenge.items():
			l.append(networkString("%s=%s" % (k, quoteString(v))))
		return b" ".join([scheme, b", ".join(l)])

	def quoteString(s):
		return b'"%s"' % (s.replace(b'\\', b'\\\\').replace(b'"', b'\\"'),)

	request.setResponseCode(401)
	for fact in self._credentialFactories:
		challenge = fact.getChallenge(request)
		request.responseHeaders.addRawHeader(
			b'www-authenticate',
			generateWWWAuthenticate(fact.scheme, challenge))
	if request.method == b'HEAD':
		return b''
	return b'Unauthorized'

UnauthorizedResource.render = render


@implementer(ICredentialsChecker)
class SuperUserChecker(InMemoryUsernamePasswordDatabaseDontUse):
	credentialInterfaces = (IUsernamePassword,
                            IUsernameHashedPassword)
	
	def __init__(self):
		config = getConfig()
		self.users = {} 
		self.coding = config.website.coding
		[ self.users.update({u.encode(self.coding):p.encode(self.coding)}) for u,p in config.website.supperusers.items() ]
		#print('superUserChecker,users=',self.users)
		
	def _cbPasswordMatch(self, matched, username):
		# print('password checking...')
		if matched:
			return username
		else:
			return failure.Failure(error.UnauthorizedLogin())

	def requestAvatarId(self, credentials):
		# print('credentials type=',type(credentials),'username=',credentials.username,type(credentials.username),'password=',credentials.password,type(credentials.password)) 
		if credentials.username in self.users:
			return defer.maybeDeferred(
				credentials.checkPassword,
				self.users[credentials.username]).addCallback(
				self._cbPasswordMatch, credentials.username)
		else:
			return defer.fail(error.UnauthorizedLogin())

class IUser(Interface):
	id = Attribute("An string value which represent logioned user")

@implementer(IUser)
class User(object):
	def __init__(self,session):
		self.id = None

registerAdapter(User,Session,IUser)

def setUser(request,uid):
	session = request.getSession()
	user = IUser(session)
	user.id = uid

def getUser(request):
	session = request.getSession()
	user = IUser(session).id
	return user
	
@implementer(IRealm)
class SimpleRealm(object):
	"""
	A realm which gives out L{GuardedResource} instances for authenticated
	users.
	"""
	#implements(IRealm)

	def __init__(self,rootObj):
		self.resource = rootObj
		
	def requestAvatar(self, avatarId, mind, *interfaces):
		if resource.IResource in interfaces:
			return resource.IResource, self.resource, lambda: None
		raise NotImplementedError()


class BaseAuthorityChecker:
	def check(user,uri):
		"""
		return True mean pass the check,False mean failed
		"""
		return False

class MyHTTPAuthSessionWrapper(HTTPAuthSessionWrapper):
	def __init__(self,root,auth_paths=['/']):
		self.auth_paths = auth_paths
		credentialFactory = BasicCredentialFactory(b'realm')
		self.portal = Portal(SimpleRealm(root), [SuperUserChecker()])
		HTTPAuthSessionWrapper.__init__(self,self.portal,[credentialFactory])
		self.authority_checkers = []

	def addAuthorityChecker(self,checker):
		self.authority_checkers.append(checker)
	
	def addUserChecker(self,checker):
		self.portal.registerChecker(checker)
		
	def _authorizedResource(self, request):
		root = self.portal.realm.resource

		request.path = unicoding(request.path)
		auth = False
		for p in self.auth_paths:
			cnt = len(p)
			if request.path[:cnt] == p:
				auth = True
				break
		user = self.getUserInfo(request).username
		setUser(request,user)
		if not auth:
			return root
		if len(self.authority_checkers)>0:
			passed = False
			for c in self.authority_checkers:
				if c(user,request.path):
					passed = True
			if not passed:
				#print(' authority failed')
				return UnauthorizedResource(self._credentialFactories)
		#print(user,request.path,self._credentialFactories)			
		return HTTPAuthSessionWrapper._authorizedResource(self,request)

	def getUserInfo(self,request):
		try:
			authheader = request.getHeader(b'authorization')
			factory, respString = self._selectParseHeader(authheader)
			return factory.decode(respString, request)
		except:
			u = Anonymous()
			u.username = 'Anonymous'
			return u

			
if __name__ == '__main__':
	from twisted.web.static import File

	home="d:/mydocs/python/pywork/static"
	class MyResource(File):
		def render(self,request):
			return File.render(self,request)


	root = MyResource(home)
	rootResource = MyHTTPAuthSessionWrapper(root,auth_paths=['/python-3.6.1'])
	site = server.Site(rootResource)
	p1 = reactor.listenTCP(8080, site,interface='0.0.0.0')
	reactor.run()

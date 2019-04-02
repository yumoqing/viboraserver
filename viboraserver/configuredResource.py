# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
import sys
import time
import ujson as json
import threading		
import traceback
import codecs

from twisted.internet import reactor
from twisted.internet import threads,defer
from twisted.web.resource import Resource
from twisted.internet import threads
from twisted.web.util import redirectTo, Redirect 
from twisted.web import server, resource, guard
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.python.components import registerAdapter
from twisted.web.server import Session
from twisted.web.script import ResourceScript
from twisted.cred import error
from twisted.web import util
from twisted.web._auth.wrapper import UnauthorizedResource
from twisted.web.resource import IResource, ErrorPage
from twisted.cred.credentials import Anonymous
from twisted.web.server import NOT_DONE_YET
from zope.interface import Interface, Attribute, implements

from patterncoding.myTemplateEngine import MyTemplateEngine

from appPublic.timeUtils import str2Date,str2Datetime,curDatetime,getCurrentTimeStamp
from appPublic.timecost import TimeCost
from appPublic.unicoding import unicoding,uDict
from appPublic.jsonConfig import getConfig
from appPublic.Singleton import GlobalEnv

from sql.sqlorAPI import DBPools

from WebServer.webUtils import getContentType
from WebServer.myResource import MyResource

from WebServer.webUtils import getClientType
from WebServer.globalEnv import abspath,absUrl,ServerException,WebsiteSessiones


FunctionList={
	#'treeTest':treeTest,
	#'treegridTest':treegridTest,
}

def addFuncList(fname,func):
	FunctionList[fname] = func

def missFunc(request):
	return "not implement yet !!!"

def getFunction(name):
	return FunctionList.get(fname,missFunc)

def errorFunc(request,errdict):
	return ujson.dumps(errdict)

class I18nResource(Resource):
	def render(self,request):
		c = getConfig()
		i = c.i18n
		lang = request.getHeader('Accept-Language').split(',')[0]
		l = c.langMapping.get(lang,lang)
		return json.dumps(i.getLangDict(l)).encode(c.website.coding)

class BaseProcessor(Resource,object):
	isLeaf = True
	def __init__(self,filename,k):
		config = getConfig()
		self.timecost = TimeCost()
		self.env = {}	
		self.src_file = unicoding(filename)
		self.json_file = self.src_file
		self.file_data = {}
		self.workdir = os.path.dirname(self.src_file)
		self.callbackList = []
		self.setCallback(self.readSource)
		
		self.headers = {}
		self.config = config
		#print('path=',self.src_file,type(self.src_file))

	def openfile(self,path,mode):
		p = abspath(path)
		if p is None:
			return None
		f = codecs.open(p,mode,self.src_coding)
		return f
			
	def readSource(self,dic={},request=None):
		self.src_coding = self.config.source_coding
		f = None
		try:
			f = codecs.open(self.src_file,'r',self.src_coding)
		except Exception as e:
			print("BaseProcessor open source()",self.src_file,e)
			raise ServerException(60001,"file read error(%s)" % self.src_file)
		try:
			self.file_data = self.fileHandle(f,request)
		except Exception as e:
			f.close()
			raise e
				
		return self.file_data
	
	def fileHandle(self,f,request):
		try:
			return json.load(f)
		except Exception as e:
			print('file:',self.src_file,e)
			raise e

	def setCallback(self,func):
		self.callbackList.append(func)
		
	def _requestFailed(self, failure,request):
		try:
			pool = DBPools()
			pool.freeAll()
			if hasattr(failure,'render'):
				return failure.render(request)
			else:
				request.processingFailed(failure)
			self.timecost.end(self.src_file)
			print('%s info(perform)::%s costs %.4lf seconds at thread id=%d' % (getCurrentTimeStamp(),request.path,self.timecost.getTimeCost(self.src_file),threading.get_ident()))
			sys.stdout.flush()
			return None
		except Exception as e:
			print('error=',e)
			sys.stdout.flush()
	
	def _final(self,data,request):
		config = getConfig()
		pool = DBPools()
		pool.freeAll()
		if request.finished:
			return
		if data is None:
			docs = ""
		if type(data)==type('') or type(data)==type(b''):
			docs = data
			ctype = getContentType(self.src_file)
		elif type(data) == type({}) and data.get('tmplname',False):
			config = getConfig()
			mydata = data
			tmplname = data.get('tmplname',None)
			mydata = data.get('data',data)
			mydata['request'] = request
			mydata['running_env'] = config.running_env
			docs = self.translate(tmplname,mydata,request)
			ctype = getContentType(self.src_file)
		else:
			docs = json.dumps(data)
			ctype = 'text/json'
		
		docs = docs.encode(config.website.coding) if not isinstance(docs,bytes) else docs

		if ctype is None:
			ctype = 'text/html'
		request.setHeader('Content-type','%s; charset=%s' % (ctype,config.website.coding))
		request.setHeader('Content-Length',len(docs))
		request.write(docs)
		request.finish()
		self.timecost.end(self.src_file)
		print('%s info(perform)::%s costs %.4lf seconds at thread id=%d' % (getCurrentTimeStamp(),request.path,self.timecost.getTimeCost(self.src_file),threading.get_ident()),'content-length=',len(docs))
		sys.stdout.flush()
		
	def srcTmplpaths(self):
		conf = getConfig()
		p = os.path.abspath(os.path.dirname(self.src_file))
		root = os.path.abspath(conf.website.root)
		ret = []
		while p.startswith(root):
			ret.append(p)
			p = os.path.dirname(p)
		return ret

	def getTemplateEngine(self,request):
		conf = getConfig()
		paths = self.srcTmplpaths()
		te = MyTemplateEngine(paths,conf.template_file_coding,conf.website.coding)
		te.env.globals.update(self.env)
		return te

	def getRequestLang(self,request):
		lang = request.getHeader('Accept-Language').split(',')[0]
		return lang
		
	def render(self,request):
		def getGlobal():
			return data
		def userid():
			ws = WebsiteSessiones()
			ss = ws.getUserid(request)
			if ss==None:
				return 'Anonymous'
			return ss
			
		def sessiondata():
			ws = WebsiteSessiones()
			d = ws.getDataSet(request)
			return d
			
		def clientType():
			return getClientType(request)
		
		def redirect(url):
			if type(url)==type(''):
				url = url.encode(self.config.website.coding)
			return redirectTo(url,request)
			
		def myI18n(s):
			c = getConfig()
			i = c.i18n
			lang = self.getRequestLang(request)
			l = c.langMapping.get(lang,lang)
			return i(s,l)
		def renders(s,d):
			te = self.getTemplateEngine(request)
			return te.renders(s,d)
			
		self.timecost.begin(self.src_file)
		
		config = getConfig()
		self.env['request'] = request
		self.env['userid'] = userid()
		self.env['terminalType'] = clientType()
		self.env['i18n'] = myI18n
		self.env['curpath'] = os.path.dirname(self.src_file)
		self.env['src_file'] = self.src_file
		self.env['openfile'] = self.openfile
		self.env['curfolder'] = self.workdir
		self.env['renders'] = renders
		self.env['redirect'] = redirect
		self.env['appname'] = config.license.app
		self.env['sessiondata'] = sessiondata
		
		session = request.getSession()
		session.touch()
		args = uDict(request.args,coding=config.website.coding)
		request.args = args
		if type(request.path) == type(b''):
			request.path = request.path.decode(config.website.coding)
		d = threads.deferToThread(self._renderInChildThread,request)
		return NOT_DONE_YET

	def _renderInChildThread(self,request):
		d = defer.maybeDeferred(self._render,request)
		for cb in self.callbackList:
			d.addCallback(cb,request)
		d.addCallback(self._final,request)
		d.addErrback(self._requestFailed,request)
		

	def _render(self,request):
		print('%s info(perform)::%s running at thread id=%d' % (
				getCurrentTimeStamp(),
				request.path,threading.get_ident()
			)
		)	
		sys.stdout.flush()
		return self.file_data


class DictScriptPythonProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='dspy'
	
	def fileHandle(self,f,request):
		b = f.read()
		b= ''.join(b.split('\r'))
		lines = b.split('\n')
		lines = ['\t' + l for l in lines ]
		txt = "def __myfunc_(request):\n" + '\n'.join(lines)
		lenv={}
		[ lenv.update({k:self.env[k]}) for k in self.env ]
		lenv['request'] = request
		try:
			ge = {}
			ge.update(GlobalEnv())
			ge.update(self.env)
			exec(txt,ge,lenv)
		except Exception as e:
			print(txt,e,'##############################################################')
			traceback.print_exc()
			raise e
		try:
			self.file_data = lenv['__myfunc_'](request)
		except Exception as e:
			print("__myfunc__() executed error",e)
			traceback.print_exc()
			raise e
		return self.file_data

class TemplateProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='tmpl'

	def fileHandle(self,f,request):
		te = self.getTemplateEngine(request)
		b = f.read()
		self.file_data = te.renders(b,request.args)
		return self.file_data

class FuncRequest(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return False
	def __init__(self,func):
		Resource.__init__(self)
		self._call = func
	
	def _render(self,request):
		return self._call(request)
		
FuncAsyncRequest = FuncRequest



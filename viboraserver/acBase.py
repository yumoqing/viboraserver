# coding: utf-8

import os
import re
import traceback
import copy
import json

from appPublic.jsonConfig import getConfig
from appPublic.MiniI18N import getI18N
from appPublic.rsa import RSA
from appPublic.dictObject import DictObject

from vibora import Vibora
from vibora.request import Request
from vibora.router import Route
from vibora.static import StaticHandler
from vibora.exceptions import StaticNotFound
from .baseProcessor import getProcessor
from .xlsxdsProcessor import XLSXDataSourceProcessor
from .sqldsProcessor import SQLDataSourceProcessor
from .serverenv import ServerEnv
from .url2file import Url2File

class MyApp(Vibora):
	def _configure_static_files(self):
		if self.static:
			static_route = Route((self.static.url_prefix + '/.*').encode(), self.static.handle,
				methods=(b'GET', b'POST', b'HEAD'), parent=self, limits=self.limits)
			self.router.add_route(static_route, {'': ''}, check_slashes=False)


class NotImplementYet(Exception):
	pass

class UserNeedLogin(StaticHandler):
	pass

def getHeaderLang(request):
	al = request.headers.get('Accept-Language')
	if al is None:
		return 'en'
	return al.split(',')[0]
	
def i18nDICT(request):
	c = getConfig()
	i18n = getI18N()
	lang = getHeaderLang(request)
	l = c.langMapping.get(lang,lang)
	return json.dumps(i18n.getLangDict(l)).encode(c.website.coding)

class RefusedResource(StaticHandler):
	async def handle(self,request:Request):
		path = self.extract_path(request)
		return path + b':refused access!'

class UnknownException(StaticHandler):
	def __init__(self,e,*args,**kwargs):
		super(UnknownException,self).__init__(*args,**kwargs)
		self.e = e
		
	def handle(self,request:Request):
		path = self.extract_path(request)
		print('Exception.....!',path,'exception=',self.e,'type e=',type(self.e))
		return path + b':exception happend'
		
class ACBase:
	"""
	网站访问控制基本类
	需要继承此类，并实现checkPassword，和checkUserPrivilege两个函数
	使用例子：
	class MyAC(ACBase):
		def checkPassword(self,user,password):
			myusers= {
				'root':'pwd123'
				'user1':'pwd123'
			}
			p = myusers.get(user,None)
			if p == None:
				return False
			if p != password:
				return False
			return True
		def checkUserPrivilege(self,user,path):
			# 用户可以做任何操作
			return True
		
	在需要控制的地方
	ac = MyAC()
	if not ac.accessCheck(request):
		#拒绝操作
	# 正常操作
	"""
	def __init__(self):
		self.conf = getConfig()
		self.rsaEngine = RSA()
		fname = self.conf.website.rsakey.privatekey
		self.privatekey = self.rsaEngine.read_privatekey(fname,'ymq123')
		
	def _selectParseHeader(self,authheader):
		txt = self.rsaEngine.decode(self.privatekey,authheader)
		return txt.split(':')
		
	def checkUserPrivilege(self,user,path):
		raise NotImplementYet

	def checkPassword(self,user,password):
		raise NotImplementYet
		
	def getRequestUserPassword(self,request):
		try:
			authheader = request.getHeader(b'authorization')
			if authheader is not None:
				return self._selectParseHeader(authheader)
			return None,None
		except Exception as e:
			return 'Anonymous',None

	def isNeedLogin(self,path):
		raise NotImplementYet
		
	def acCheck(self,request):
		path = self.resource.extract_path(request)
		ws = WebsiteSessiones()
		user =  ws.getUserid(request)
		if user == None:
			user,password = self.getRequestUserPassword(request)
			if user is None:
				raise UserNeedLogin(path)
			if not self.checkPassword(user,password):
				raise UserNeedLogin(path)
			ws.login(request,user)
	
		if not self.checkUserPrivilege(user,path):
			raise UnauthorityResource()
		return True
		
	def accessCheck(self,request: Request):
		"""
		检查用户是否由权限访问此url
		"""
		path = self.resource.extract_path(request)
		if self.isNeedLogin(path):
			# print('need login')
			return self.acCheck(request)
		#没在配置文件设定的路径不做控制，可以随意访问
		# print('not need login')
		return True
        
class BaseResource(StaticHandler,Url2File):
	def __init__(self,paths: list, indexes: list=[], accessController=None):
		StaticHandler.__init__(self,paths=paths,url_prefix='')
		Url2File.__init__(self,paths,indexes,inherit=True)
		super(BaseResource,self).__init__(paths=paths,url_prefix='')
		self.processors = {}
		self.indexes = indexes
		self.app = None
		self.access_controller = accessController
		if accessController is not None:
			self.access_controller.resource = self
		self.env = DictObject()

	def setApp(app):
		self.app = app

	def abspath(self,path:str):
		for rpath in self.paths:
			rp = rpath + path
			real_path = os.path.abspath(rp)
			if os.path.isfile(real_path):
				return real_path
		return None

	async def _handle(self,request:Request):
		path = self.extract_path(request)
		realpath = self.url2file(path)
		if realpath is None:
			print(f'realpath={realpath} not found')
			raise StaticNotFound()
			
		for k,name in self.processors:
			if realpath.endswith(k):
				klass = getProcessor(name)
				h = klass(realpath,self)
				return await h.handle(request)
		return await super(BaseResource,self).handle(request)
		
	def getGetArgs(self,request:Request):
		ret = {}
		c = getConfig()
		coding = c.website.coding
		for k,v in request.args.items():
			k = k.decode(c.website.coding)
			if len(v) > 1:
				v = [i.decode(c.website.coding) for i in v]
			else:
				v = v[0].decode(c.website.coding)
			ret[k] = v
		return ret

	async def handle(self,request:Request):
		clientkeys = {
			"iPhone":"iphone",
			"iPad":"ipad",
			"Android":"androidpad",
			"Windows Phone":"winphone",
			"Windows NT[.]*Win64; x64":"pc",
		}

		def i18nDICT():
			c = getConfig()
			g = ServerEnv()
			if not g.get('myi18n',False):
				g.myi18n = getI18N()
			lang = getHeaderLang(request)
			l = c.langMapping.get(lang,lang)
			return json.dumps(g.myi18n.getLangDict(l))

		def getClientType(request):
			agent = request.headers.get('user-agent')
			if type(agent)!=type('') and type(agent)!=type(b''):
				return 'pc'
			for k in clientkeys.keys():
				m = re.findall(k,agent)
				if len(m)>0:
					return clientkeys[k]
			return 'pc'

		def serveri18n(s):
			lang = getHeaderLang(request)
			c = getConfig()
			g = ServerEnv()
			if not g.get('myi18n',False):
				g.myi18n = getI18N()
			l = c.langMapping.get(lang,lang)
			return g.myi18n(s,l)

		def getArgs():
			return self.getGetArgs(request)
		self.env.i18n = serveri18n
		self.env.i18nDict = i18nDICT
		self.env.terminalType = getClientType(request)
		self.env.absurl = self.absUrl
		self.env.abspath = self.abspath
		self.env.request2ns = getArgs
		self.env.resource = self

		path = self.extract_path(request)
		print(f'handle {path}..',request.method)
		if self.access_controller is None:
			return await self._handle(request)

		if self.access_controller.accessCheck(request):
			return await self._handle(request)

		raise UserNeedLogin

	def absUrl(self,request,url):
		http='http://'
		https='https://'
		if url[:7] == http:
			return url
		if url[:8] == https:
			return url

		path = self.extract_path(request)
		return self.relatedurl(path,url)


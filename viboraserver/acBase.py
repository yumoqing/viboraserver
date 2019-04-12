# coding: utf-8

import os
import re
import traceback
import copy
import json

from appPublic.jsonConfig import getConfig
from appPublic.MiniI18N import getI18N
from appPublic.rsa import RSA

from vibora.request import Request
from vibora.static import StaticHandler
from vibora.exceptions import StaticNotFound
from .baseProcessor import getProcessor
from .xlsxdsProcessor import XLSXDataSourceProcessor
from .sqldsProcessor import SQLDataSourceProcessor
from .serverenv import ServerEnv
from .globalEnv import envsetted

class NotImplementYet(Exception):
	pass

class UserNeedLogin(StaticHandler):
	pass

def i18nDICT(request):
	c = getConfig()
	i18n = getI18N()
	lang = request.headers.get('Accept-Language').split(',')[0]
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
		
	def accessCheck(self,request):
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
        
class BaseResource(StaticHandler):
	def __init__(self,paths,accessController=None):
		super(BaseResource,self).__init__(paths=paths,url_prefix='')
		self.processors = {}
		self.indexes = []
		self.access_controller = accessController
		if accessController is not None:
			self.access_controller.resource = self

	def endsWith(self,f,s):
		f = f.encode('utf-8') if hasattr(f,'encode') else f
		s = s.encode('utf-8') if hasattr(f,'encode') else s
		return endsWith(f.lower(),s.lower())

	def abspath(self,path):
		for rpath in self.paths:
			real_path = rpath + path
			if os.path.isfile(real_path):
				return real_path
		return None

	def requestPaths(self,request):
		path = self.extract_path(request)
		for rpath in self.paths:
			real_path = rpath + path
			if os.path.isfile(real_path):
				return path.split('/')[:-1]
			if os.path.isdir(real_path):
				return path.split('/')
		return []

	async def _handle(self,request:Request):
		path = self.extract_path(request)
		if path[-1] == '/':
			path = path[:-1]
		for root_path in self.paths:
			real_path = root_path + path
			if os.path.isdir(real_path):
				p = None
				for f in self.indexes:
					pp = os.path.join(real_path,f)
					if self.exists(pp):
						p = pp
						break
				if p is not None:
					real_path = p
			if self.exists(real_path):
				for k,name in self.processors:
					if endsWith(real_path,k):
						klass = getProcessor(name)
						h = klass(real_path,self)
						return h.handle(request)
				return await super(BaseResource,self).handle(request)
		print(f'real_path={real_path} not found')
		raise StaticNotFound()
		
	def getPostArgs(self,request):
		ret = self.getGetArgs(request)
		print('getPostArgs(),args=',ret)
		ret = request.form()
		return ret

	def getGetArgs(self,request):
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
			lang = request.headers.get('Accept-Language').split(',')[0]
			l = c.langMapping.get(lang,lang)
			return json.dumps(g.myi18n.getLangDict(l))

		def getClientType(request):
			agent = request.headers.get('user-agent')
			for k in clientkeys.keys():
				m = re.findall(k,agent)
				if len(m)>0:
					return clientkeys[k]
			return 'pc'

		def serveri18n(s):
			lang = request.headers.get('Accept-Language').split(',')[0]
			c = getConfig()
			g = ServerEnv()
			if not g.get('myi18n',False):
				g.myi18n = getI18N()
			l = c.langMapping.get(lang,lang)
			return g.myi18n(s,l)

		def getArgs():
			return self.getGetArgs(request)
			if request.method == b'GET':
				return self.getGetArgs(request)
			else:
				return self.getPostArgs(request)
		g = ServerEnv()
		g.i18n = serveri18n
		g.i18nDict = i18nDICT
		g.terminalType = getClientType(request)
		g.absurl = self.absUrl
		g.abspath = self.abspath
		g.request = request
		g.request2ns = getArgs
		g.resource = self

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

		paths = self.requestPaths(request)
		if url[0] == '/':
			return url
		for d in url.split('/'):
			if d == '' or d is None:
				continue
			if d == '.':
				continue
			if d == '..':
				paths = paths[:-1]
				continue
			paths.append(d)
		ret = '/'.join(paths)
		if url[-1]=='/':
			ret = ret + '/'
		return ret


# coding: utf-8

import os
import traceback
import copy

from appPublic.jsonConfig import getConfig
from appPublic.folderUtils import endsWith
from appPublic.rsa import RSA
from WebServer.globalEnv import UserNeedLogin,WebsiteSessiones

from vibora.request import Request
from vibora.static import StaticHandler
from vibora.exceptions import StaticNotFound
from .baseProcessor import getProcessor

class NotImplementYet(Exception):
    pass

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

	def absUrl(self,request,url):
		http='http://'
		https='https://'
		if url[:7] == http:
			return url
		if url[:8] == https:
			return url

		paths = self.extract_path(request).split('/')[:-1]
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

	def add_processor(self,id,Klass):
		self.processors[id] = Klass

	async def _handle(self,request:Request):
		path = self.extract_path(request)
		if path[-1] == '/':
			path = path[:-1]
		for root_path in self.paths:
			real_path = root_path + path
			if self.exists(real_path):
				if os.path.isdir(real_path):
					p = None
					for f in self.indexes:
						pp = os.path.join(real_path,f)
						print(f'pp=',pp)
						if self.exists(pp):
							p = pp
							break
					if p is not None:
						real_path = p
					
				for k in self.processors.keys():
					print(f'real_path={real_path},k={k}')
					if endsWith(real_path,k):
						name = self.processors[k]
						klass = getProcessor(name)
						h = klass(real_path,self)
						return h.handle(request)
				print('no processor defined,using parent class')
				return await super(BaseResource,self).handle(request)
		print(f'path={path},real_path={real_path}')
		raise StaticNotFound()
		
	async def handle(self,request:Request):
		print('handle....')
		if self.access_controller is None:
			return await self._handle(request)

		if self.access_controller.accessCheck(request):
			return await self._handle(request)

		raise UserNeedLogin


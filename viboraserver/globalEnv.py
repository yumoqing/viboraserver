# -*- coding:utf8 -*-
import os
import sys
import codecs 
from urllib.parse import quote
import ujson as json

import random
import time
import datetime
from openpyxl import Workbook
from tempfile import mktemp

from twisted.web.resource import Resource
from twisted.web.util import redirectTo

from appPublic.jsonConfig import getConfig
from appPublic.Singleton import GlobalEnv
from appPublic.argsConvert import ArgsConvert
from appPublic.timeUtils import str2Date,str2Datetime,curDatetime,getCurrentTimeStamp
from appPublic.folderUtils import folderInfo
from appPublic.uniqueID import setNode,getID
from appPublic.unicoding import unicoding,uDict,uObject
from appPublic.Singleton import SingletonDecorator

from sql.crud import _CRUD,CRUD
from sql.sqlorAPI import DBPools,sqlorFactory,getSqlorByName,closeSqlorByName,runSQL,runSQLPaging,runSQLIterator,getTables,getTableFields,getTablePrimaryKey,getTableForignKeys,runSQLResultFields


from WebServer.xlsxData import XLSXData
from WebServer.webUtils import getClientType
from WebServer.uriop import URIOp

class Data(object):
	def __init__(self):
		super(Data,self).__init__()
		self._data_ = {}
		
	def set(self,k,v):
		self._data_[k] = v
	
	def get(self,k,dv=None):
		return self._data_.get(k,dv)

	def __del__(self):
		for k in self._data_.keys():
			del self._data_[k]
		
class SessionStatus(Data):
	def __init__(self,sid,userid):
		super(SessionStatus,self).__init__()
		self.sid = sid
		self.userid = userid
	
	def getUserid(self):
		return self.userid
			
@SingletonDecorator
class WebsiteSessiones:
	def __init__(self):
		self.statuses = {}
		self.data = {}
	
	def getSessionStatus(self,request):
		sess = request.getSession()
		sid = sess.uid
		ss =  self.statuses.get(sid,None)
		return ss
		
	def getDataSet(self,request):
		sess = request.getSession()
		sid = sess.uid
		d = self.data.get(sid,None)
		if d is None:
			d = Data()
			self.data[sid] = d
		return d
	
	def getData(self,k,request):
		d = self.getDataSet(request)
		return d.get(k)
	
	def setData(self,k,v,request):
		d = self.getDataSet(request)
		d.set(k,v)
		
	def getUserid(self,request):
		ss = self.getSessionStatus(request)
		if ss is not None:
			return ss.getUserid()
		return None
		
	def login(self,request,userid):
		sess = request.getSession()
		sid = sess.uid
		sess.notifyOnExpire(lambda: self.logout)
		self.statuses[sid] = SessionStatus(sid,userid)
		
	def logout(self,request):
		sid = request.getSession().uid
		try:
			del self.statuses[sid]
		except:
			pass
	
class SuccessHint(Resource):
	def __init__(self,func,hint):
		self.funcname = func
		self.msg = hint
	
	def __str__(self):
		return json.dumps({
			"status":"OK",
			"funcname":self.funcname,
			"msg":self.msg
		},indent=4)

	def render(self,request):
		message = str(self)
		message = message.encode(self.config.website.coding)
		return message
		
class ServerException(Resource,Exception):
	def __init__(self,errcode,errmessage):
		self.errcode = errcode
		self.errmsg = errmessage
		super(ServerException,self).__init__()
	
	def render(self,request):
		config = getConfig()
		message = str(self)
		message = message.encode(config.website.coding)
		return message
		
	def __str__(self):
		return json.dumps({
			"status":"error",
			"errorcode":self.errcode,
			"errmsg":self.errmsg
		},indent=4)

class UserNeedLogin(ServerException):
	def __init__(self,url):
		super(UserNeedLogin,self).__init__(69999,'User need login')
		config = getConfig()
		if type(url) == type(''):
			url = url.encode(config.website.coding)
		self.url = url
	
	def render(self,request):
		ch = request.getHeader(b'X-Requested-With')
		# print('X-Requested-With=',ch)
		"""
		for k,v in request.requestHeaders.getAllRawHeaders():
			print(k,'=',v)
		"""
		if ch==b'XMLHttpRequest':
			# a ajax call
			# print('ajax access')
			config = getConfig()
			message = str(self)
			message = message.encode(config.website.coding)
			# print('ajax request, return=',message)
			return message
		# print('normal access')
		return redirectTo(b"/login.tmpl?url=" + self.url,request)
		
	def __str__(self):
		conf = getConfig()
		d = {
			"status":"error",
			"errorcode":69999,
			"errmsg":'Unauthorized'
		}
		return json.dumps(d,indent=4)
	
class UnauthorityResource(ServerException):
	def __init__(self):
		super(UnauthorityResource,self).__init__(69998,'unauthority resource')
	
def data2xlsx(rows,headers=None):
	wb = Workbook()
	ws = wb.active

	i = 1
	if headers is not None:
		for j in range(len(headers)):
			v = headers[j].title if headers[j].get('title',False) else headers[j].name
			ws.cell(column=j+1,row=i,value=v)
		i += 1
	for r in rows:
		for j in range(len(r)):
			v = r[headers[j].name]
			ws.cell(column=j+1,row=i,value=v)
		i += 1
	name = mktemp(suffix='.xlsx')
	wb.save(filename = name)
	wb.close()
	return name
	
class FileOutZone(Exception):
	def __init__(fp,*args,**kwargs):
		super(FileOutZone,self).__init__(*args,**kwargs)
		self.openfilename = fp
	
	def __str__(self):
		return self.openfilename + ': not allowed to open'
		
def openfile(fp,m):
	conf = getConfig()
	fs = [os.path.abspath(i) for i in conf.allowed_folders ]
	fs.append(os.path.abspath(conf.website.root))
	x = os.path.abspath(fp)
	r = False
	for f in fs:
		if x.startswith(f):
			r = True
			break
	if not r:
		raise FileOutZone(x)
	return open(x,m)
	
def isNone(a):
	return a is None

def obj2JsonString(obj,coding='utf-8'):
	if type(obj) == type([]):
		return """[
	%s
]""" % ','.join([obj2JsonString(i,coding) for i in obj ])
	if type(obj) == type({}):
		return """{
%s
}""" % ','.join(['"%s":%s' % (k,obj2JsonString(v,coding)) for k,v in obj.items() ])

	if obj is None:
		return 'null'
	if hasattr(obj,'encode'):
		obj = obj.encode(coding)
	if type(obj) == type(''):
		if len(obj) > 17 and obj[:8] == '<nquote>' and obj[-9:] == '</nquote>':
			return obj[8:-9]
		else:
			return '"%s"' % obj
	else:
		return str(obj)

def absUrl(request,url):
	http='http://'
	https='https://'
	if url[:7] == http:
		return url
	if url[:8] == https:
		return url

	paths = request.path.split('/')[:-1]
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

def abspath(path):
	config = getConfig()
	root = os.path.abspath(config.website.root)
	if path[0] == '/':
		path=path[1:]
	p = os.path.join(root,path)
	if not p.startswith(root):
		return None
	return p

def appname():
	config = getConfig()
	return config.license.app
	
def request2ns(request):
	ret = {}
	for k,v in request.args.items():
		if type(v) == type([]) and len(v) == 1:
			ret[k] = v[0]
		else :
			ret[k] = v
	ret = uObject(ret)
	return ret

def configValue(ks):
	config = getConfig()
	try:
		a = eval('config' + ks)
		return a
	except:
		return None

def visualcoding():
	return configValue('.website.visualcoding');

def file_download(request,path,name,coding='utf8'):
	f = openfile(path,'rb')
	b = f.read()
	f.close()
	fname = quote(name).encode(coding)
	hah = b"attachment; filename=" + fname
	# print('file head=',hah.decode(coding))
	request.setHeader(b'Content-Disposition',hah)
	request.setHeader(b'Expires',0)
	request.setHeader(b'Cache-Control',b'must-revalidate, post-check=0, pre-check=0')
	request.setHeader(b'Content-Transfer-Encoding',b'binary')
	request.setHeader(b'Pragma',b'public')
	request.setHeader(b'Content-Length',len(b))
	request.write(b)
	request.finish()
	
globalFunctions = {
	'configValue':configValue,
	'visualcoding':visualcoding,
	"uriop":URIOp,
	'isNone':isNone,
	'json':json,
	"int":int,
	"str":str,
	"float":float,
	"type":type,
	"ArgsConvert":ArgsConvert,
	'time':time,
	'datetime':datetime,
	'random':random,
	'absurl':absUrl,
	'obj2json':obj2JsonString,
	'str2date':str2Date,
	'str2datetime':str2Datetime,
	'curDatetime':curDatetime,
	'ServerException':ServerException,
	'uObject':uObject,
	'uuid':getID,
	'getSqlor':getSqlorByName,
	"closeSqlor":closeSqlorByName,
	'runSQL':runSQL,
	'runSQLPaging':runSQLPaging,
	'runSQLIterator':runSQLIterator,
	'runSQLResultFields':runSQLResultFields,
	'getTables':getTables,
	'getTableFields':getTableFields,
	'getTablePrimaryKey':getTablePrimaryKey,
	'getTableForignKeys':getTableForignKeys,
	'folderInfo':folderInfo,
	'abspath':abspath,
	#"uriop":URIOp,
	"request2ns":request2ns,
	"CRUD":CRUD,
	"_CRUD":_CRUD,
	"data2xlsx":data2xlsx,
	"xlsxdata":XLSXData,
	"download":file_download,
	"SuccessHint":SuccessHint
}



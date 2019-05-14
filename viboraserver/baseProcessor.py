import os
import re
import json
import codecs
from jinja2 import Template,Environment,BaseLoader

from appPublic.jsonConfig import getConfig
from appPublic.dictObject import DictObject
from appPublic.folderUtils import listFile

from vibora.responses import Response,CachedResponse
from vibora.request import Request
from .serverenv import ServerEnv

class ObjectCache:
	def __init__(self):
		self.cache = {}

	def store(self,path,obj):
		o = self.cache.get(path,None)
		if o is not None:
			try:
				del o.cached_obj
			except:
				pass
		o = DictObject()
		o.cached_obj = obj
		o.mtime = os.path.getmtime(path)
		self.cache[path] = o

	def get(self,path):
		o = self.cache.get(path)
		if o:
			if os.path.getmtime(path) > o.mtime:
				return None
			return o.cached_obj
		return None

		
class BaseProcessor:
	@classmethod
	def isMe(self,name):
		return name=='base'

	def __init__(self,path,resource):
		self.path = path
		self.resource = resource
		self.retResponse = None
		self.last_modified = os.path.getmtime(path)
		self.content_length = os.path.getsize(path)
		self.headers = {
			'Content-Type': 'text/html',
			'Content-Length': str(self.content_length),
			'Accept-Ranges': 'bytes'
		}

	
	async def handle(self,request):
		config = getConfig()
		await self.datahandle(request)
		if self.retResponse is not None:
			return self.retResponse
		if type(self.content) == type({}):
			self.content = json.dumps(self.content,
				indent=4)
		if type(self.content) == type([]):
			self.content = json.dumps(self.content,
				indent=4)
		self.content = self.content if isinstance(self.content,bytes) else self.content.encode('utf-8')
		self.setheaders()
		return CachedResponse(self.content,headers=self.headers)

	async def datahandle(self,txt,request):
		print('*******Error*************')
		self.content=''

	def setheaders(self):
		self.headers['Content-Length'] = str(len(self.content))

class TemplateProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='tmpl'

	async def datahandle(self,request):
		path = self.resource.extract_path(request)
		g = ServerEnv()
		ns = DictObject()
		ns.update(g)
		ns.update(self.resource.env)
		ns.request = request
		ns.ref_real_path = self.path
		te = g.tmpl_engine
		self.content = te.render(path,**ns)
		#self.content = await te.render_async(path,**ns)
		
	def setheaders(self):
		super(TemplateProcessor,self).setheaders()
		if self.path.endswith('.tmpl.css'):
			self.headers['Content-Type'] = 'text/css; utf-8'
		elif self.path.endswith('.tmpl.js'):
			self.headers['Content-Type'] = 'application/javascript ; utf-8'
		else:
			self.headers['Content-Type'] = 'text/html; utf-8'


class PythonScriptProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='dspy'

	async def loadScript(self):
		data = ''
		with codecs.open(self.path,'rb','utf-8') as f:
			data = f.read()
		b= ''.join(data.split('\r'))
		lines = b.split('\n')
		lines = ['\t' + l for l in lines ]
		txt = "async def __myfunc_(request,**ns):\n" + '\n'.join(lines)
		g = ServerEnv()
		lenv = {}
		lenv.update(g)
		lenv.update(self.resource.env)
		exec(txt,lenv,lenv)
		f = lenv['__myfunc_']
		return f
		
	async def datahandle(self,request):
		g = ServerEnv()
		if not g.get('dspy_cache',False):
			g.dspy_cache = ObjectCache()
		func = g.dspy_cache.get(self.path)
		if not func:
			func = await self.loadScript()
			g.dspy_cache.store(self.path,func)
		lenv = {}
		lenv.update(g)
		lenv.update(self.resource.env)
		self.content = await func(request,**lenv)

class MarkdownProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='md'

	async def datahandle(self,request:Request):
		data = ''
		with codecs.open(self.path,'rb','utf-8') as f:
			data = f.read()
		b = data
		b = self.urlreplace(b,request)
		ret = {
				"__widget__":"markdown",
				"data":{
					"md_text":b
				}
		}
		config = getConfig()
		self.content = json.dumps(ret,indent=4)

	def urlreplace(self,mdtxt,request):
		def replaceURL(s):
			p1 = '\[.*?\]\((.*?)\)'
			url = re.findall(p1,s)[0]
			txts = s.split(url)
			url = self.resource.absUrl(request,url)
			return url.join(txts)

		p = '\[.*?\]\(.*?\)'
		textarray = re.split(p,mdtxt)
		links = re.findall(p,mdtxt)
		newlinks = [ replaceURL(link) for link in links]
		if len(links)>0:
			mdtxt = ''
			for i in range(len(newlinks)):
				mdtxt = mdtxt + textarray[i]
				mdtxt = mdtxt + newlinks[i]
			mdtxt = mdtxt + textarray[i+1]
		return mdtxt



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

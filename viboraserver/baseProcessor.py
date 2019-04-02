import os
import re
import codecs
from appPublic.folderUtils import endsWith
from vibora.responses import Response,CachedResponse
from .serverenv import ServerEnv

class BaseProcessor:
	@classmethod
	def isMe(self,name):
		return name=='base'

	def __init__(self,path,resource):
		self.path = path
		self.resource = resource
		self.last_modified = os.path.getmtime(path)
		self.content_length = os.path.getsize(path)
		self.headers = {
			'Content-Type': 'text/html',
			'Content-Length': str(self.content_length),
			'Accept-Ranges': 'bytes'
		}

	
	def handle(self,request):
		with codecs.open(self.path,'r','utf-8') as f:
			self.datahandle(f.read(),request)
		self.content = self.content if isinstance(self.content,Bytes) else self.content.encode('utf-8')
		self.setheaders()
		return Response(self.content,self.headers)

	def setheaders(self):
		self.headers['Content-Length'] = str(len(self.content))

	def datahandle(self):
		pass

class TemplateProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='tmpl'

	def datahandle(self,data,request):
		g = ServerEnv()
		ns = request.args
		self.content = g.tmplRender.renders(data,ns)	
		
	def setheaders(self):
		super(TemplateProcessor,self).setheaders()
		if endsWith(self.path,'.css.tmpl'):
			self.headers['Content-Type'] = 'text/css; utf-8'
		elif endsWith(self.path,'.js.tmpl'):
			self.headers['Content-Type'] = 'text/js; utf-8'
		else:
			self.headers['Content-Type'] = 'text/html; utf-8'


class PythonScriptProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='dspy'

	def datahandle(self,data,request):
		b= ''.join(data.split('\r'))
		lines = b.split('\n')
		lines = ['\t' + l for l in lines ]
		txt = "def __myfunc_(request):\n" + '\n'.join(lines)
		lenv={}
		g = ServerEnv()
		[ lenv.update({k:g[k]}) for k in g.keys() ]
		lenv['object'] = self
		lenv['request'] = request
		try:
			exec(txt,lenv,lenv)
		except Exception as e:
			print(txt,e,'#################################')
			traceback.print_exc()
			raise e
		try:

			self.content = lenv['__myfunc_'](request)
		except Exception as e:
			print("__myfunc__() executed error",e)
			traceback.print_exc()
			raise e

class MarkdownProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='md'

	def datahandle(self,data,request):
		b = data
		b = self.urlreplace(b,request)
		ret = {
				"__widget__":"markdown",
				"data":{
					"md_text":b
				}
		}
		self.file_data = ret
		return self.file_data

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

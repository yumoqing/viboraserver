import codecs
from appPublic.folderUtils import endsWith
from vibora.responses import Response,CachedResponse
from .serverenv import ServerEnv

class BaseProcessor:
        @classmethod
        def isMe(self,name):
                return name=='base'
        
	def __init__(self,path):
		self.path
		self.content_type = self.mime.guess_type(path)
		self.last_modified = os.path.getmtime(path)
		self.content_length = os.path.getsize(path)
		self.headers = {
			'Content-Type': self.content_type[0],
			'Content-Length': str(self.content_length),
			'Accept-Ranges': 'bytes'
		}

	
	def handle(self,request):
		with codecs.open(path,'r','utf-8') as f	
			self.datahandle(f.read(),request)
		self.content = self.content if isinstance(self.content,Bytes) else self.content.encode('utf-8')
		self.setheaders()
		return Response(self.content,self.headers)

	def setheaders(self):
		self.headers[Content-Length'] = str(len(self.content))

	def datahandle(self):
		pass

class TemplateProcessor(BaseProcessor):
        @classmethod
        def isMe(self,name):
                return name=='tmpl'
        
	def datahandle(self,data,request):
		g = getSeverEnv()
		ns = request.args
		self.content = g.tmplRender.renders(data,ns)	
		
	def setheaders(self):
		super(TemplateProcessor,self).setheaders()
		if endsWith(self.path,'.css.tmpl'):
			self.headers['Content-Type'] = 'text/css; utf-8'
		else if endsWith(self.path,'.js.tmpl'):
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
                return name=='dspy'

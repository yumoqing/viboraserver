from twisted.web import static 
from appPublic.unicoding import unicoding

class MyResource(static.File):
	def __init__(self, path, defaultType="text/html", ignoredExts=(), registry=None, allowExt=0):
		path = unicoding(path)
		super(MyResource,self).__init__(path, defaultType=defaultType, ignoredExts=ignoredExts, registry=registry, allowExt=allowExt)
		
	def getChild(self,path,request):
		path = unicoding(path)

		res = self.children.get(path,None)
		if res is not None:
			return res
		
		return static.File.getChild(self,path,request)
	
	def render(self,request):
		session = request.getSession()
		session.touch()
		return static.File.render(self,request)
		
	def render_POST(self,request):
		session = request.getSession()
		session.touch()
		request.path = unicoding(request.path)
		return static.File.render_GET(self,request)
	

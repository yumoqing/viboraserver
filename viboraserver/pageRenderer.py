# pageRenderer.py
import os
from acResource import AuthorityControlResource
from appPublic.jsonConfig import getConfig
from webUtils import getClientType
from appPublic.jsonConfig import JsonObject

class PageRenderer(AuthorityControlResource):
	"""
	this is a Web Page render class, which use a json input file and a template file to generate a web page.
	the PageRenderer is a processor for file suffixed by ".page"
	the .page file is a json formated file its charset is utf-8
	"""
	isLeaf = 1
	def __init__(self,jsonfile,registery):
		if type(jsonfile) == type(u" "):
			jsonfile = jsonfile.encode('utf-8')
		self.jsonfile = jsonfile
		self.registery = registery
		self.obj = JsonObject(self.jsonfile)
		
	
	def _render(self,request):
		client = getClientType(request);
		config = getConfig()
		coding = config.website.coding
		adapter = config.website.clientAdapter.get(client,config.website.clientAdapter.get("default"))
		te = adapter.myTemplateEngine
		tmplname = getattr(self.obj,"template_name",'page.tmpl')
		print( "template name=",tmplname)
		docs = te.render(tmplname,self.obj)
		request.write(docs)
		request.finish()
		return docs


import codecs
import json
from appPublic.jsonConfig import getConfig
from appPublic.dictObject import DictObject
from .baseProcessor import BaseProcessor
from .serverenv import ServerEnv

class DataSourceProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='ds'
		
	def __init__(self,filename,k):
		super(DataSourceProcessor,self).__init__(filename,k)
		self.actions = {
			'getdata':self.getData,
			'pagingdata':self.getPagingData,
			'arguments':self.getArgumentsDesc,
			'resultFields':self.getDataDesc,
			'gridlist':self.getGridlist,
		}
		self.g = ServerEnv()
		
	def getData(self,dict_data,ns,request):pass
	def getPagingData(self,dict_data,ns,request):pass
	def getArgumentsDesc(self,dict_data,ns,request):pass
	def getDataDesc(self,dict_data,ns,request):pass
	def getGridlist(self,dict_data,ns,request):
		ret = self.getDataDesc(dict_data,ns,request)
		ffs = [ f for f in ret if f.get('frozen',False) ]
		fs = [ f for f in ret if not f['frozen'] ]
		[ f.update({'hide':True}) for f in ffs if f.get('listhide',False) ]
		[ f.update({'hide':True}) for f in fs if f.get('listhide') ]
		d = {
			"iconCls":"icon-search",
			"url":self.resource.absUrl(request,request.path + '?action=pagingdata'),
			"view":"bufferview",
			"options":{
				"pageSize":50,
				"pagination":False
			}
		}
		d.update({'fields':fs})
		if len(ffs)>0:
			d.update({'ffields':ffs})
		ret = {
				"__ctmpl__":"datagrid",
				"data":d
		}
		return ret

	async def datahandle(self,request):
		dict_data = {}
		config = getConfig()
		with codecs.open(self.path,'r',config.website.coding) as f:
			b = f.read()
			dict_data = json.loads(b)
		ns = DictObject()
		g = ServerEnv()
		ns.update(g)
		ns.update(self.resource.env)
		ns.update(self.resource.getGetArgs(request))
		act = ns.get('action','getdata')
		action = self.actions.get(act)
		self.content = action(dict_data,ns,request)
		
	

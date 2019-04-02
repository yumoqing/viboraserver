
from appPublic.jsonConfig import getConfig
from WebServer.configuredResource import BaseProcessor
from WebServer.globalEnv import request2ns,absUrl

class DataSourceProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='ds'
		
	def getArgumentsDesc(self,dict_data,ns,request):
		return dict_data
	
	def getDataDesc(self,dict_data,ns,request):
		return dict_data
	
	def getData(self,dict_data,ns,request):
		return dict_data
	
	def getPagingData(self,dict_data,ns,request):
		return dict_data

	def getGridlist(self,dict_data,ns,request):
		return dict_data
	
	def __init__(self,filename,k):
		super(DataSourceProcessor,self).__init__(filename,k)
		self.actions = {
			'getdata':self.getData,
			'pagingdata':self.getPagingData,
			'arguments':self.getArgumentsDesc,
			'resultFields':self.getDataDesc,
			'gridlist':self.getGridlist,
		}
		self.setCallback(self.dataHandler)
		
	def getGridlist(self,dict_data,ns,request):
		ret = self.getDataDesc(dict_data,ns,request)
		ffs = [ f for f in ret if f.get('frozen',False) ]
		fs = [ f for f in ret if not f['frozen'] ]
		[ f.update({'hide':True}) for f in ffs if f.get('listhide',False) ]
		[ f.update({'hide':True}) for f in fs if f.get('listhide') ]
		d = {
			"iconCls":"icon-search",
			"url":absUrl(request,request.path + '?action=pagingdata'),
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

	def dataHandler(self,dict_data,request):
		ns = request2ns(request)
		self.file_data = dict_data
		act = ns.get('action','getdata')
		action = self.actions.get(act)
		return action(dict_data,ns,request)
		
	

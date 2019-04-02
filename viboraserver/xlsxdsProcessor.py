import codecs

from openpyxl import load_workbook

from appPublic.jsonConfig import getConfig

from WebServer.globalEnv import abspath,absUrl
from WebServer.dsProcessor import DataSourceProcessor
from WebServer.xlsxData import XLSXData

"""
xlsxds file format:
{
	"xlsxfile":"./data.xlsx",
	"data_from":7,
	"data_sheet":"Sheet1",
	"label_at",1,
	"name_at":null,
	"datatype_at":2,
	"ioattrs":3,
	"listhide_at":4,
	"inputhide_at":5,
	"frozen_at":6
}
"""

class XLSXDataSourceProcessor(DataSourceProcessor):
	@classmethod
	def isMe(self,name):
		return name=='xlsxds'
		
	def dataHandler(self,dict_data,request):
		self.file_data = dict_data
		path = dict_data.get('xlsxfile',None)
		if path is None:
			raise Exception('xlsxfile not defined in xlsxds file')
			
		self.xlsxdata = XLSXData(abspath(absUrl(request,path)),dict_data)
		return super(XLSXDataSourceProcessor,self).dataHandler(dict_data,request)
		
	def getArgumentsDesc(self,dict_data,ns,request):
		return None

	def getDataDesc(self,dict_data,ns,request):
		ret = self.xlsxdata.getBaseFieldsInfo(ns)
		return ret

	def getData(self,dict_data,ns,request):
		ret = self.xlsxdata.getData(ns)
		return ret

	def getPagingData(self,dict_data,ns,request):
		ret = self.xlsxdata.getPagingData(ns)
		return ret
		

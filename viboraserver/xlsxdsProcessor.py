import codecs

from openpyxl import load_workbook

from appPublic.jsonConfig import getConfig

from .dsProcessor import DataSourceProcessor
from .xlsxData import XLSXData

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
		
	def getArgumentsDesc(self,dict_data,ns,request):
		return None

	def getDataDesc(self,dict_data,ns,request):
		path = dict_data.get('xlsxfile',None)
		self.xlsxdata = XLSXData(self.g.abspath(self.g.absurl(request,path)),dict_data)
		ret = self.xlsxdata.getBaseFieldsInfo(ns)
		return ret

	def getData(self,dict_data,ns,request):
		path = dict_data.get('xlsxfile',None)
		self.xlsxdata = XLSXData(self.g.abspath(self.g.absurl(request,path)),dict_data)
		ret = self.xlsxdata.getData(ns)
		return ret

	def getPagingData(self,dict_data,ns,request):
		path = dict_data.get('xlsxfile',None)
		self.xlsxdata = XLSXData(self.g.abspath(ns.absurl(request,path)),dict_data)
		ret = self.xlsxdata.getPagingData(ns)
		return ret
		

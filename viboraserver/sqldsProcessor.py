import codecs
from .dsProcessor import DataSourceProcessor
from appPublic.jsonConfig import getConfig
from sqlor.dbpools import DBPools
import  json
"""
sqlds file format:
{
	"sqldesc":{
		"sql_string":"select * from dbo.stock_daily_hist where stock_num=${stock_num}$ order by trade_date desc",
		"db":"mydb",
		"sortfield":"stock_date"
	}
	"arguments":[
		{
			"name":"stock_num",
			"type":"str",
			"iotype":"text",
			"default":"600804"
		}
	],
	"datadesc":[
		{
		}
	]
}
"""

class SQLDataSourceProcessor(DataSourceProcessor):
	@classmethod
	def isMe(self,name):
		return name=='sqlds'
	
	def getArgumentsDesc(self,dict_data,ns,request):
		desc = dict_data.get('arguments',None)
		return desc
		
	def getDataDesc(self,dict_data,ns,request):
		pool = DBPools()
		@pool.runSQLResultFields
		def sql(dbname,NS):
			sqldesc = dict_data.get('sqldesc')
			# print('sql(),sqldesc=',sqldesc)
			return sqldesc
		rec = dict_data.get('datadesc',None)
		if rec is None:
			sqldesc = dict_data.get('sqldesc')
			ns = dict_data.get('arguments',{})
			rec = [ r for r in sql(sqldesc['db'],ns) if r['name']!='_row_id' ]
			dict_data['datadesc'] = rec
			f = codecs.open(self.src_file,'w',self.config.website.coding)
			b = json.dumps(dict_data,indent=4)
			f.write(b)
			f.close()
		return rec

	def getData(self,dict_data,ns,request):
		pool = DBPools()
		@pool.runSQL
		def sql(dbname,NS):
			sqldesc = dict_data.get('sqldesc')
			return sqldesc
		db = dict_data['sqldesc']['db']
		ret = [ i for i in sql(db,ns) ]
		return ret
		
	def getPagingData(self,dict_data,ns,request):
		pool = DBPools()
		@pool.runSQLPaging
		def sql(dbname,NS):
			sqldesc = dict_data.get('sqldesc')
			return sqldesc
		db = dict_data['sqldesc']['db']
		ret = sql(db,ns)
		return ret

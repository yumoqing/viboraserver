import re
from appPublic.jsonConfig import getConfig
from WebServer.configuredResource import BaseProcessor
from WebServer.globalEnv import request2ns,absUrl

class MarkDownProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='md'
		
	content_type='webwidget/json'

	def fileHandle(self,f,request):
		b = f.read()
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
			url = absUrl(request,url)
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
		

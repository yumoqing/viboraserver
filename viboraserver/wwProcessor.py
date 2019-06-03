from appPublic.jsonConfig import getConfig
from WebServer.configuredResource import BaseProcessor
from WebServer.globalEnv import request2ns,absUrl

class WebWidgetProcessor(BaseProcessor):
	@classmethod
	def isMe(self,name):
		return name=='ww'
		
		
	

# fileUpload.py

import cgi
import os

from appPublic.folderUtils import _mkdir
from appPublic.jsonConfig import getConfig

class TmpFileSaver:
	def __init__(self):
		config = getConfig()
		self.root = config.tmproot
	
	def _name2path(name):
		name = os.path.basename(name)
		paths=[191,193,197,199]
		b = name.encode('utf8') if not isinstance(name,bytes) else name
		v = int.from_bytes(b,byteorder='big',signed=False)
		path = os.path.abspath(os.path.join(self.root,
					v % paths[0],
					v % paths[1],
					v % paths[2],
					v % paths[3],
					name))
		return path

	def save(name,data):
		p = self.name2path(name)
		_mkdir(os.path.dirname(p))
		data = data.encode('utf8') if not isinstance(data,bytes) else data
		f = open(p,'wb')
		f.write(data)
		f.close()
		return p


		
class UpFile:
	def __init__(self,request,handler):
		headers = request.getAllHeaders()
		self.obj =  cgi.FieldStorage(
			fp = request.content,
			headers = headers,
			environ = {
				'REQUEST_METHOD':'POST',
				'CONTENT_TYPE': self.headers['content-type'],
			}
		)
		self.handler = handler
	
	def handle(self,fieldname):
		return self.handler(self.obj[fieldname].filename,self.obj[fieldname].value)



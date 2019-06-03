#
import os
import codecs
from appPublic.jsonConfig import getConfig
from appPublic.folderUtils import folderInfo

class URIopException(Exception):
	def __init__(self,errtype,errmsg):
		self.errtype = errtype
		self.errmsg = errmsg
		super(URIopException,self).init('errtype=%s,errmsg=%s' % (errtype,errmsg))
		
	def __str__(self):
		return 'errtype=%s,errmsg=%s' % (self.errtype,self.errmsg)
		
class URIOp(object):
	def __init__(self):
		self.conf = getConfig()
		self.realPath = os.path.abspath(self.conf.website.root)
	
	def abspath(self,uri=None):
		p = self.conf.website.root
		if uri is not None and len(uri)>0:
			x = uri
			if x[0] == '/':
				x = x[1:]
			p = os.path.join(p,*x.split('/'))
		d = os.path.abspath(p)
		if len(d) < len(self.realPath):
			raise URIopException('url scope error',uri);
		if d[:len(self.realPath)] != self.realPath:
			raise URIopException('url scope error',uri);
		return d
		
	def fileList(self,uri=''):
		r = [ i for i in folderInfo(self.realPath,uri) ]
		for i in r:
			if i['type']=='dir':
				i['state'] = 'closed'
			i['id'] = '_#_'.join(i['id'].split('/'))

		ret={
			'total':len(r),
			'rows':r
		}
		return ret
		
	def mkdir(self,at_uri,name):
		p = self.abspath(at_uri)
		p = os.path.join(p,name)
		os.mkdir(p)
	
	def rename(self,uri,newname):
		p = self.abspath(uri)
		dir = os.path.dirname(p)
		np = os.path.join(p,newname)
		os.rename(p,np)
		
	def delete(self,uri):
		p = self.abspath(uri)
		os.remove(p)
	
	def save(self,uri,data):
		p = self.abspath(uri)
		f = codecs.open(p,"w",self.conf.website.coding)
		f.write(data)
		f.close()
		
	
	def read(self,uri):
		p = self.abspath(uri)
		f = codecs.open(p,"r",self.conf.website.coding)
		b = f.read()
		f.close()
		return b

	def write(self,uri,data):
		p = self.abspath(uri)
		f = codecs.open(p,"w",self.conf.website.coding)
		f.write(data)
		f.close()

				
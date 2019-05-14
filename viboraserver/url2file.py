

import os

class Url2File:
	def __init__(self,paths: list,indexes: list, inherit: bool=False):
		self.paths = paths
		self.indexes = indexes
		self.inherit = inherit

	def realurl(self,url):
		items = url.split('/')
		items = [ i for i in items if i != '.' ]
		while '..' in items:
			for i,v in enumerate(items):
				if v=='..' and i > 0:
					del items[i]
					del items[i-1]
					break
		return '/'.join(items)

	def isFolder(self,url: str):
		for r in self.paths:
			rp = r + url
			real_path = os.path.abspath(rp)
			if os.path.isdir(real_path):
				return True
		return False

	def defaultIndex(self,url: str):
		for p in self.indexes:
			rp = url + '/' + p
			r = self.url2file(rp)
			if r is not None:
				return r
		return None

	def url2file(self,url: str):
		if url[-1] == '/':
			url = url[:-1]

		if self.isFolder(url):
			return self.defaultIndex(url)

		for r in self.paths:
			f = r + url
			real_path = os.path.abspath(f)
			if os.path.isfile(real_path):
				return f
		if not self.inherit:
			return None
		items = url.split('/')
		if len(items) > 2:
			del items[-2]
			url = '/'.join(items)
			return self.url2file(url)
		return None

	def relatedurl(self,url: str, name: str):
		if url[-1] == '/':
			url = url[:-1]

		if not self.isFolder(url):
			items = url.split('/')
			del items[-1]
			url = '/'.join(items)
		url = url + '/' + name
		return self.realurl(url)

	def relatedurl2file(self,url: str, name: str):
		url = self.relatedurl(url,name)
		return self.url2file(url)

class TmplUrl2File(Url2File):
	def __init__(self,paths,indexes, subffixes=['.tmpl'],inherit=False):
		Url2File.__init__(self,paths,indexes=indexes,inherit=inherit)
		self.subffixes = subffixes

	def list_tmpl(self):
		ret = []
		for rp in self.paths:
			p = os.path.abspath(rp)
			[ ret.append(i) for i in listFile(p,suffixs=self.subffixes,rescursive=True) ]	
		return sorted(ret)


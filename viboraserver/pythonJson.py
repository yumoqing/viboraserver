import os, traceback

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO
	
from twisted.web import http, server, static, resource, html
from appPublic.jsonIO import jsonEncode,jsonDecode
from appPublic.ExecFile import DictConfig

class PythonJson(resource.Resource):
	"""I am an extremely simple dynamic resource; an embedded python json data.
	This will execute a file (usually of the extension '.pyjson') as Python code,
	internal to the webserver.
	"""
	
	isLeaf = 1
	def __init__(self, filename, registry):
		"""Initialize me with a script name.
		"""
		self.filename = filename
		self.registry = registry

	def render(self, request):
		"""Render me to a web client.

		Load my file, execute it in a special namespace (with 'request' and
		'__file__' global vars) and finish the request.  Output to the web-page
		will NOT be handled with print - standard output goes to the log - but
		with request.write.
		"""
		request.setHeader("x-powered-by","Twisted/14")
		namespace = {'request': request,
					 '__file__': self.filename,
					 'registry': self.registry}
		try:
			f = open(self.filename,'r')
			buf = f.read()
			f.close()
			mystr = "__tmp_variable = %s" % buf
			dc = DictConfig(excstr=mystr)
			d = dc.__tmp_variable
			return jsonEncode(d)
			# execfile(self.filename, namespace, namespace)
		except IOError as e:
			if e.errno == 2: #file not found
				request.setResponseCode(http.NOT_FOUND)
				request.write(resource.NoResource("File not found.").render(request))
		except:
			io = StringIO.StringIO()
			traceback.print_exc(file=io)
			request.write(html.PRE(io.getvalue()))


import json

from acResource import AuthorityControlResource
from twisted.web.resource import Resource
FunctionList={
	#'treeTest':treeTest,
	#'treegridTest':treegridTest,
}

def addFuncList(fname,func):
	FunctionList[fname] = func

def missFunc(request):
	return "not implement yet !!!"

def errorFunc(request,errdict):
	return json.dumps(errdict)
	
class FuncResource(AuthorityControlResource):
	def __init__(self,func):
		AuthorityControlResource.__init__(self)
		self._call = func
	
	def _render(self,request):
		return self._call(request)
		
FuncAsyncFuncResource = FuncResource
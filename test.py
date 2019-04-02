from viboraserver.acBase import BaseResource

from vibora import Vibora

resource = BaseResource(paths=['/home/ymq/ext/pydev/front/myclient',
			'/home/ymq/ext/pydev/front/samples',
			'/home/ymq/ext/pydev/front/usepkgs'
		])
print('herere.........')
app = Vibora( static = resource)
print('herere.........')

app.run(debug=True,host='0.0.0.0',port=8080)

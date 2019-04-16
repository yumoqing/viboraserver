import os

from appPublic.Singleton import SingletonDecorator
from vibora.templates.template import Template
from vibora.templates.ast import merge, raise_nodes
from vibora.templates import TemplateEngine
from vibora.templates.nodes import ExtendsNode, MacroNode
from vibora.templates.template import Template, TemplateParser, ParsedTemplate, CompiledTemplate

from vibora.templates.nodes import BlockNode, MacroNode, IncludeNode, Node

from .serverenv import ServerEnv
from .url2file import Url2File

@SingletonDecorator
class MyTemplateEngine(TemplateEngine):

	def __init__(self,paths,indexes):
		TemplateEngine.__init__(self)
		self.url2file = Url2File(paths,indexes)

	def resolve_include_nodes(self,realpath,nodes: list) -> list:
		# nodes = template.ast.children
		relationships = []
		for index, node in enumerate(nodes):
			if isinstance(node, IncludeNode):
				target = self.get_template(realpath,node.target)
				relationships.append(target)
				self.prepare_template(target)
				nodes[index] = target.ast
			elif node.children:
				inner_relationships = self.resolve_include_nodes(realpath,node.children)
				relationships += inner_relationships
		return relationships

	async def _render(self,name: str,streaming: bool=False,**template_vars):
		return await TemplateEngine.render(self,name,
				streaming=streaming,
				template_vars=template_vars)

	async def render(self,name: str,streaming: bool=False,**template_vars):
		template = self.templates.get(name,None)
		if template is None:
			self.load_new_template(name)
		return await self._render(name,streaming=streaming,**template_vars)

	def load_new_template(self,name: str):
		fn = self.url2file.url2file(name)
		if fn is None:
			raise Exception(f'{name} not found')

		with open(fn, 'r') as f:
			template = Template(f.read())
			parsed_template = self.add_template(template,[name])
			parsed_template.realpath = name
			self.prepare_template(parsed_template)
			compiled_template = self.compiler.compile(parsed_template)
			self.cache.store(compiled_template)
			self.compiled_templates[parsed_template.hash] = compiled_template

	def prepare_template(self, template: ParsedTemplate):
		if template.prepared:
			return

		#for extension in self.extenions:
		#	extension.before_prepare(self,template)

		relationships = self.resolve_include_nodes(template.realpath,template.ast.children)
		for t in relationships:
			template.dependencies.append(t.hash)

		for index, node in enumerate(template.ast.children):
			if isinstance(node, ExtendsNode):
				parent = self.get_template(template.realpath,node.parent)
				template.dependencies.add(parent.hash)
				self.prepare_template(parent)
				template.ast = merge(parent,template)
		raise_nodes(lambda x: isinstance(x, MacroNode), template.ast)
		template.prepared = True

	def get_template(self,curpath,name:str):
		url = self.url2file.relatedurl(curpath,name)
		if url is None:
			raise Exception(f'relatedurl({curpath},{name}) not found')

		template = self.templates.get(url)
		if not template:
			self.load_new_template(url)
		return self.templates.get(url)

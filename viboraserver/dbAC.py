# -*- coding:utf8 -*-
from WebServer.acBase import ACBase
from sql.sqlorAPI import runSQL,runSQLIterator
from sql.crud import _CRUD
from appPublic.rc4 import RC4
from appPublic.uniqueID import getID

class DatabaseAC(ACBase):
	"""
	使用ac_xxxx八张表来控制用户访问权限
	"""
	def __init__(self,db,encryptKey):
		super(DatabaseAC,self).__init__()
		self.db = db
		self.encryptKey = encryptKey
		self.rc4 = RC4(encryptKey)
		
	def checkPassword(self,user,password):
		"""
		用userid和加密后的密码组合条件查询ac_users表中的用户记录，查到则用户认证成功，否则失败
		"""
		@runSQLIterator
		def sql(db,ns):
			desc = {
				"sql_string":"""select * 
				from ac_users 
				where user_id = ${user_id}$ and 
						userpwd = ${password}$ and
						userstatus = '1'
				"""
			}
			return desc
		# 加密密码
		pwd = self.rc4.encode(user + ':' + password)
		ns = {'user_id':user,'password':pwd}
		s = [ i for i in sql(self.db,ns) ]
		return len(s) > 0
		
	def checkUserPrivilege(self,user,path):
		"""
		检查用户是否拥有path所代表的功能的权限，如果ac_userpermission表中存在用户与功能对，
		  或ac_rolepermission表中存在用户的任一角色与功能对，则用户拥有此功能权限。
		"""
		@runSQLIterator
		def sql(db,ns):
			desc = {
				"sql_string":"""
				select 'ok' as url
					from ac_users a
						inner join ac_userrole b
							on a.user_id = b.user_id
						inner join ac_roles c
							on b.role_id = c.role_id
					where c.rolename = 'superuser' and a.user_id = ${user_id}$ and a.userstatus = '1'
				union
				select e.url 
					from ac_rolepermission a
						inner join ac_userrole x
							on a.role_id = x.role_id
						inner join ac_users b
							on x.user_id = b.user_id
						inner join ac_permissions c
							on a.perm_id = c.perm_id
						inner join ac_funcpermission d
							on c.perm_id = d.perm_id
						inner join ac_functions e
							on d.func_id = e.func_id
					where e.url = ${url}$ and b.user_id = ${user_id}$
				union
				select  e.url
					from ac_rolepermission a
						inner join ac_userrole x
							on a.role_id = x.role_id
						inner join ac_users b
							on x.user_id = b.user_id
						inner join ac_permissions c
							on a.perm_id = c.perm_id
						inner join ac_funcpermission d
							on c.perm_id = d.perm_id
						inner join ac_functions e
							on d.func_id = e.func_id
					where e.url = ${url}$ and b.user_id = ${user_id}$
				"""
			}
			return desc
		s = [i for i in sql(self.db,{"url":path,"user_id":user})]
		return len(s) > 0
		
	def isNeedLogin(self,path):
		"""
		检查路径是否在ac_functions表中，如果不在则返回false，不需要用户登录，任何人可以访问
		"""
		@runSQLIterator
		def sql(db,ns):
			desc = {
				"sql_string":"select * from ac_functions where url=${url}$"
			}
			return desc
		s = [i for i in sql(self.db,{"url":path})]
		f = len(s)>0
		# print('path(%s) need login:' % path,f)
		return f
	
	def addUser(self,userid,username,password):
		@runSQL
		def sql(db,ns):
			desc = {
				"sql_string":"""insert into ac_users 
				(user_id,username,userpwd,userstatus) 
				values 
				(${user_id}$,${username}$,${userpwd}$,'1')"""
			}
			return desc
		assert len(userid) <= 32
		pwd = self.rc4.encode(userid + ':' + password)
		ns = {
			"user_id":userid,
			"username":username,
			"userpwd":pwd
		}
		sql(self.db,ns)
		return ns
		
	def addRole(self,roleName):
		@runSQL
		def sql(db,ns):
			desc = {
				"sql_string":"""insert into ac_roles (role_id,rolename) values (${role_id}$,${rolename}$)"""
			}
			return desc
		
		ns = {
			"role_id":getID(),
			"rolename":roleName
		}
		sql(self.db,ns)
		return ns
		
	def addFunction(self,fname,url):
		@runSQL
		def sql(db,ns):
			desc = {
				"sql_string":"""
				insert into ac_functions 
				(func_id,url,functionname)
				values
				(${func_id}$,${url}$,${functionname}$)
				"""
			}
			return desc
		
		ns = {
			"func_id":getID(),
			"url":url,
			"functionname":fname
		}
		sql(self.db,ns)
		return ns
		
	def addPermission(self,pname):
		@runSQL
		def sql(db,ns):
			desc = {
				"sql_string":"""
				insert into ac_permissions 
				(perm_id,p_name)
				values
				(${perm_id}$,${p_name}$)
				"""
			}
			return desc
			
		ns = {
			"perm_id":getID(),
			"p_name":pname
		}
		sql(self.db,ns)
		return ns
		
	def addUserRole(self,userid,roleid):
		crud = _CRUD(self.db,'ac_userrole')
		ns = {
			"ur_id":getID(),
			"user_id":userid,
			"role_id":roleid
		}
		crud.C(ns)
		return ns
		
	def addFunctionPermission(self,funcid,permid):
		crud = _CRUD(self,db,'ac_funcpermission')
		ns = {
			"fp_id":getID(),
			"func_id":funcid,
			"perm_id":permid
		}
		crud.C(ns)
		return ns
		
	def addUserPermission(self,userid,permid):
		crud = _CRUD(self,db,'ac_userpermission')
		ns = {
			"up_id":getID(),
			"user_id":userid,
			"perm_id":permid
		}
		crud.C(ns)
		return ns
		
	def addRolePermission(self,roleid,permid):
		crud = _CRUD(self,db,'ac_rolepermission')
		ns = {
			"rp_id":getID(),
			"role_id":roleid,
			"perm_id":permid
		}
		crud.C(ns)
		return ns
		
if __name__ == '__main__':
	from appPublic.jsonConfig import getConfig
	from sql.sqlorAPI import DBPools
	p = 'd:/run'
	conf = getConfig(p)
	DBPools(conf.databases)
	ac = DatabaseAC('metadb',conf.encryptkey)
	#ns1 = ac.addUser('root','根用户','ymq123')
	#ns2 = ac.addRole('superuser')
	#ns3 = ac.addUserRole(ns1['user_id'],ns2['role_id'])
	ups = [
		['root','ymq123'],
		['root','YYYY'],
		['rrrr','ymq123']
	]
	rc4_1 = RC4(conf.encryptkey)
	rc4_2 = RC4(conf.encryptkey)
	for a in ups:
		#print(a[1],rc4_1.encode(a[1])==rc4_2.encode(a[1]))
		print(a[0],a[1],ac.checkPassword(a[0],a[1]))
	

# viboraserver

extend vibora with the following:
* user authorizations class
* processor for registed file type
* pre-defined variables and function can be called by processors
* DBPools and SQL wrap
* config file stored at ./conf/config.json json
* i18n support
* processors include:
	+ 'dspy' file subffix by '.dspy', is process as a python script
	+ 'tmpl' files subffix by '.tmpl', is process as a template
	+ 'md' files subffix by '.md', is process as a markdown file
	+ 'xlsxds' files subffix by '.xlsxds' is process as a data source from xlsx file
	+ 'sqlds' files subffixed by '.sqlds' is process as a data source from database via a sql command

## Requirements

[vibora](https://github.com/vibora-io/vibora)

[pyutils](https://github.com/yumoqing/pyutils)

[sqlor](https://github.com/yumoqing/sqlor)

## How to use
sample.py
```import os
import sys
from viboraserver.configuredserver import ConfiguredServer
from appPublic.folderUtils import ProgramPath
from appPublic.jsonConfig import getConfig

if __name__ == '__main__':
        program_path = ProgramPath()
        workdir = program_path
        if len(sys.argv)>1:
                workdir = sys.argv[1]
        config = getConfig(path=workdir,NS={'workdir':workdir,'ProgramPath':program_path})
        server = ConfiguredServer()
        server.run()
```

## Folder structure

+ app
+ |-sample.py
+ |--viboraserver
+ |-conf
+      |-config.json
+ |-i18n

## Configuration file content
viboraserver using json file format in its configuration, the following is a sample:
```
{
        "debug":true,
        "databases":{
		"aiocfae":{
                        "driver":"aiomysql",
			"async_mode":true,
                        "coding":"utf8",
                        "dbname":"cfae",
                        "kwargs":{
                                "user":"test",
                                "db":"cfae",
                                "password":"test123",
                                "host":"localhost"
                        }
		},
		"cfae":{
                        "driver":"mysql.connector",
                        "coding":"utf8",
                        "dbname":"cfae",
                        "kwargs":{
                                "user":"test",
                                "db":"cfae",
                                "password":"test123",
                                "host":"localhost"
                        }
		}
        },
        "website":{
                "paths":[
                        "/path/to/path1",
                        "/path/to/path2",
                        "/path/to/path3",
                        "/path/to/path4"
                ],
                "host":"0.0.0.0",
                "port":8080,
                "coding":"utf-8",
                "indexes":[
                        "index.html",
                        "index.tmpl",
                        "index.dspy",
                        "index.md"
                ],
                "visualcoding":{
                        "default_root":"/vc/test",
                        "userroot":{
                                "ymq":"/vc/ymq",
                                "root":"/vc/root"
                        },
                        "jrjpath":"/vc/default"
                },
                "processors":[
                        [".xlsxds","xlsxds"],
                        [".sqlds","sqlds"],
                        [".tmpl.js","tmpl"],
                        [".tmpl.css","tmpl"],
                        [".html.tmpl","tmpl"],
                        [".tmpl","tmpl"],
                        [".dspy","dspy"],
                        [".md","md"]
                ]
        },
        "langMapping":{
                        "zh-Hans-CN":"zh-cn",
                        "zh-CN":"zh-cn",
                        "en-us":"en",
                        "en-US":"en"
        }
}
```
### run mode configuration
if want viboraserver running in debug mode, just add a key-value pairs in config.json
```
        "debug":true,
```
else just delete this key-value in config.json in conf folder

### database configuration
viboraserver support database data operations, corrently, it ***ONLY*** support synchronous DBAPI2. 
the viboraserver using packages for database engines are:
* oracle:cx_Oracle
* mysql:mysql-connector
* postgresql:psycopg2
* sql server:pymssql

however, you can change it, but must change the "driver" value the the package name in the database connection definition.

in the databases section in config.json, you can define one or more database connection, and also, it support many database engine, just as ORACLE,mysql,postgreSQL.
define a database connnect you need follow the following json format.

* mysql or mariadb
```
                "metadb":{
                        "driver":"mysql.connector",
                        "coding":"utf8",
                        "dbname":"sampledb",
                        "kwargs":{
                                "user":"user1",
                                "db":"sampledb",
                                "password":"user123",
                                "host":"localhost"
                        }
                }
```
the dbname and "db" should the same, which is the database name in mysql database
* Oracle
```
		"db_ora":{
			"driver":"cx_Oracle",
			"coding":"utf8",
			"dbname":sampledb",
			"kwargs":{
				"user":"user1",
				"host":"localhost",
				"dsn":"10.0.185.137:1521/SAMPLEDB"
			}
		}
```

* SQL Server
```
                "db_mssql":{
                        "driver":"pymssql",
                        "coding":"utf8",
                        "dbname":"sampledb",
                        "kwargs":{
                                "user":"user1",
                                "database":"sampledb",
                                "password":"user123",
                                "server":"localhost",
                                "port":1433,
                                "charset":"utf8"
                        }
                }
```
* PostgreSQL
```
		"db_pg":{
			"driver":"psycopg2",
			"dbname":"testdb",
			"coding":"utf8",
			"kwargs":{
				"database":"testdb",
				"user":"postgres",
				"password":"pass123",
				"host":"127.0.0.1",
				"port":"5432"
			}
		}
```
### website configuration
#### paths
viboraserver can serve its contents (static file, dynamic contents render by its processors) resided on difference folders in the server file system.
viboraserver finds a content identified by http url in order the of the paths specified by "paths" lists inside "website" definition of config.json file
#### processors
all the prcessors viboraserver using, must be listed here.
#### host
by defaualt, '0.0.0.0'
#### port
by default, 8080
#### coding
viboraserver recomments using 'utf-8'
#### indexes
default content file names, viboraserver will use first found file names in the folder

### langMapping

the browsers will send 'Accept-Language' are difference even if the same language. so viboraserver using a "langMapping" definition to mapping multiple browser lang to same i18n file


## international

viboraserver using MiniI18N in appPublic modules in pyutils package to implements i18n support

it will search translate text in ms* txt file in folder named by language name inside i18n folder in workdir folder, workdir is the folder where the viboraserver program resided or identified by command line paraments.

## performance

You can find "Hello world" performance about viboraserver in [vibora](https://github.com/vibora-io/vibora)  main page

viboraserver will list and performance test for its processors later
### test macheine
xiaomi pro 15.6 i7 cpu, 16Gb memory,m2 256G disk
os: ubuntu 18.4
vibora 0.0.7
### static file
```
Running 30s test @ http://localhost:8080/swift/books/hub/welcome.htm
  12 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    24.53ms   25.42ms 461.06ms   95.70%
    Req/Sec     1.50k   320.16     4.00k    69.29%
  533944 requests in 30.10s, 414.67MB read
  Socket errors: connect 0, read 177, write 0, timeout 0
  Non-2xx or 3xx responses: 162164
Requests/sec:  17740.03
Transfer/sec:     13.78MB
```

welcome.htm file size:
```
-rw-rw-r-- 1 ymq ymq   952 12月 12  2017 welcome.htm
```
### dspy processor

```
Running 30s test @ http://localhost:8080/estate/functionlists.dspy
  12 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    35.18ms   17.45ms 187.20ms   73.62%
    Req/Sec     0.96k   230.18     2.16k    66.82%
  343789 requests in 30.09s, 726.22MB read
Requests/sec:  11426.72
Transfer/sec:     24.14MB
```

functionlists.dspy
```
selfserv = [
	{
		"funcid":"0.1",
		"text":"用户注册"
	},
	{
		"funcid":"0.2",
		"text":"用户签到"
	},
	{
		"funcid":"0.3",
		"text":"修改密码"
	},
	{
		"funcid":"0.4",
		"text":"用户签退"
	},
]

saving = [
	{
		"funcid":"1.1",
		"text":"我的存房"
	},
	{
		"funcid":"1.2",
		"text":"存房收藏"	
	},
	{
		"funcid":"1.3",
		"text":"不动产录入"	
	}
]

rentfin = [
	{
		"funcid":"3.1",
		"text":"融房收藏"
	},
	{
		"funcid":"3.2",
		"text":"我的融房"
	},
	{
		"funcid":"3.3",
		"text":"新增融房"
	},
	{
		"funcid":"3.4",
		"text":"融房标准协议"
	},
	{
		"funcid":"3.5",
		"text":"打包资产"
	}
]
return [
	{
		"funcid":"99",
		"text":"首页"
	},
	{
		"funcid":"0",
		"text":"自服务",
		"state":"open",
		"children":selfserv
	},
	{
		"funcid":"1",
		"text":"存房",
		"state":"open",
		"children":saving
	},
	{
		"funcid":"2",
		"text":"优房"
	},
	{
		"funcid":"3",
		"text":"融房",
		"state":"open",
		"children":rentfin
	},
	{
		"funcid":"4",
		"text":"获房"
	},
	{
		"funcid":"5",
		"text":"运房"
	},
	{
		"funcid":"6",
		"text":"出房"
	}
]
```

### Data read from database

Test performance for asynchronous dbapi2 driver, here is aiomysql
```
wrk -c400 -d30s -t4 http://localhost/asql.dspy
Running 30s test @ http://localhost/asql.dspy
  4 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   189.76ms  137.67ms   1.82s    77.66%
    Req/Sec   401.46     63.01   660.00     72.29%
  47950 requests in 30.07s, 188.03MB read
  Non-2xx or 3xx responses: 13
Requests/sec:   1594.83
Transfer/sec:      6.25MB
```
asql.dspy(aiomysql)
```
@runSQLPaging
def sql(db,ns):
        return {

                "sql_string":"select * from product"
        }

return await sql('aiocfae',{"page":1,"rows":10,"sort":"productid"})
```
and synchronous dbapi2 driver(mysql-connector)
```
wrk -c400 -d30s -t4 http://localhost/sql.dspy
Running 30s test @ http://localhost/sql.dspy
  4 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   221.07ms   80.60ms 687.16ms   72.53%
    Req/Sec   351.23    121.12   686.00     66.67%
  41997 requests in 30.06s, 164.73MB read
Requests/sec:   1397.07
Transfer/sec:      5.48MB
```
sql.dspy(mysql-connector)
```
@runSQLPaging
def sql(db,ns):
        return {

                "sql_string":"select * from product"
        }

return await sql('cfae',{"page":1,"rows":10,"sort":"productid"})
```
### tmpl processor

```
Running 30s test @ http://localhost:8080/estate/saving/index.tmpl
  12 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    27.53ms   14.34ms 172.99ms   73.75%
    Req/Sec     1.23k   294.38     2.57k    67.73%
  441885 requests in 30.09s, 246.53MB read
Requests/sec:  14685.00
Transfer/sec:      8.19MB
```

/estate/saving/index.tmpl is:
```
{
    "__ctmpl__":"layout",
    "data":{
        "regions":{
            "north":{
                "height":"50px",
                "remoteWidgets":[
                    "{{absurl(request,'./searchform.tmpl')}}"
                ]
            },
            "center":{
                "remoteWidgets":[
                    "{{absurl(request,'./estateView.tmpl')}}"
                ]

            }
        }
    },
    "__metadata__":{
        "__jename__":"layout"
    }
}
```
## environment for processors

When coding in processors, viboraserver provide some environment stuff for build apllication, there are modules, functions, classes and variables


### modules:
* time
* datetime
* random
* json

### functions:
* configValue
* isNone
* int
* str
* float
* type
* str2date
* str2datetime
* curDatetime
* uuid
* runSQL
* runSQLPaging
* runSQLIterator
* runSQLResultFields
* getTables
* getTableFields
* getTablePrimaryKey
* getTableForignKeys
* folderInfo
* abspath
* request2ns
* CRUD
* data2xlsx
* xlsxdata
* openfile
* i18n
* i18nDict
* absurl
* abspath
* request2ns

### variables
* resource
* terminalType

### classes
* ArgsConvert

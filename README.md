# viboraserver

extend vibora with the following:
* user authorizations class
* processor for registed file type
* pre-defined variables and function can be called by processors
* DBPools and SQL wrap
* config file stored at ./conf/config.json
* i18n support
* processors include:
	+ 'dspy' file subffix by '.dspy', is process as a python script
	+ 'tmpl' files subffix by '.tmpl', is process as a template
	+ 'md' files subffix by '.md', is process as a markdown file
	+ 'xlsxds' files subffix by '.xlsxds' is process as a data source from xlsx file
	+ 'sqlds' files subffixed by '.sqlds' is process as a data source from database via a sql command

## dependences
[vibora](https://github.com/vibora-io/vibora)
[pyutils](https://github.com/yumoqing/pyutils)

## configuration file content
viboraserver using json file format in its configuration, the following is a sample:
```
{
        "debug":true,
        "databases":{
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




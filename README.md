# Super Database 3000

## Install:
* pip install superdatabase3000

## Usage:
* first, launch a server:
```shell
from superdatabase3000 import DbServer

server = DbServer()
server.read_loop()
```

* connect client:
```shell
from superdatabase3000 import DbClient

client = DbClient()
df = client.select("/toto")
```

# Super Database 3000

| Branch | Build | Coverage | Doc | Package |
|-|-|-|-|-|
| `master` | [![Build Status](https://travis-ci.org/JeanMax/superdatabase3000.svg?branch=master)](https://travis-ci.org/JeanMax/superdatabase3000) | [![Coverage Status](https://coveralls.io/repos/github/JeanMax/SuperDatabase3000/badge.svg?branch=master)](https://coveralls.io/github/JeanMax/SuperDatabase3000?branch=master) | [![Documentation Status](https://readthedocs.org/projects/superdatabase3000/badge/?version=master)](http://superdatabase3000.readthedocs.io/en/latest/?badge=master) | [![PyPI version](https://badge.fury.io/py/superdatabase3000.svg)](https://badge.fury.io/py/superdatabase3000) |
| `dev` | [![Build Status](https://travis-ci.org/JeanMax/superdatabase3000.svg?branch=dev)](https://travis-ci.org/JeanMax/superdatabase3000) | [![Coverage Status](https://coveralls.io/repos/github/JeanMax/SuperDatabase3000/badge.svg?branch=dev)](https://coveralls.io/github/JeanMax/SuperDatabase3000?branch=dev) | [![Documentation Status](https://readthedocs.org/projects/superdatabase3000/badge/?version=dev)](http://superdatabase3000.readthedocs.io/en/latest/?badge=dev) |-|




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

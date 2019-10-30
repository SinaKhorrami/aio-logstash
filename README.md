# aio-logstash
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aio-logstash)
[![CircleCI](https://img.shields.io/circleci/build/github/SinaKhorami/aio-logstash/master)](https://circleci.com/gh/SinaKhorami/aio-logstash/tree/master)
[![PyPI version](https://badge.fury.io/py/aio-logstash.svg)](https://badge.fury.io/py/aio-logstash)

python asyncio logstash logger adapter

## Installation
```Shell
pip install aio-logstash
```
## Usage
```python
import logging
import asyncio
from aio_logstash.handler import TCPHandler

async def main():
    handler = TCPHandler()
    await handler.connect('127.0.0.1', 5000)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info('test', extra={'foo': 'bar'})

    await handler.exit()


if __name__ == '__main__':
    asyncio.run(main())
```
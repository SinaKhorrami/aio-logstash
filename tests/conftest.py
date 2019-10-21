import asyncio
import json
import pytest


class FakeServer:

    def __init__(self):
        self.server = None
        self.data = None

    async def run(self):
        self.server = await asyncio.start_server(
            self.on_connect,
            host='127.0.0.1'
        )

    async def on_connect(self, reader, writer):
        data = await reader.readline()
        data = data.decode('utf8')

        print(f"Received {data}")
        self.data = json.loads(data)

    async def close(self):
        if self.server is None:
            return

        self.server.close()
        await self.server.wait_closed()
        self.server = None

    async def get_data(self):
        while True:
            if self.data:
                return self.data
            await asyncio.sleep(0.1)

    @property
    def port(self):
        return self.server.sockets[0].getsockname()[1]


@pytest.fixture
async def make_server():
    servers = list()

    async def _make_server():
        server = FakeServer()

        await server.run()

        servers.append(server)

        return server

    yield _make_server

    async def _finalize():
        for server in servers:
            await server.close()

    await _finalize()


@pytest.fixture
async def make_handler(make_server):
    handlers = list()

    async def _make_handler():
        from aio_logstash.handler import TCPHandler

        server = await make_server()
        handler = TCPHandler()

        await handler.connect(
            host='127.0.0.1',
            port=server.port
        )

        handlers.append(handler)

        return handler, server

    yield _make_handler

    async def _finalize():
        for handler in handlers:
            await handler.exit()

    await _finalize()


@pytest.fixture
async def make_logger(make_handler):
    async def _make_logger():
        import logging

        handler, server = await make_handler()
        logger = logging.getLogger('aio-logstash_test')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        return logger, handler, server

    yield _make_logger

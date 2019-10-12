import abc
import asyncio
import logging
from aio_logstash.formatter import V1Formatter


class BaseHandler(logging.Handler):

    def __init__(self, num_consumers=1):
        super().__init__()
        self.setFormatter(V1Formatter())
        self._retry_timeout = 1
        self._queue = asyncio.Queue()
        self._consumers = [
            asyncio.create_task(self._consumer()) for _ in range(num_consumers)
        ]

    def _produce(self, item):
        self._queue.put_nowait(item)

    def emit(self, record):
        self._produce(record)

    def _serialize(self, record):
        return self.format(record) + b'\n'

    async def _consumer(self):
        while True:
            record = await self._queue.get()

            data = self._serialize(record)

            while True:
                try:
                    await self._send(data)
                    break
                except (OSError, RuntimeError):
                    await self._reconnect()

            self._queue.task_done()

    @abc.abstractmethod
    async def _send(self, data):
        pass

    @abc.abstractmethod
    async def _disconnect(self):
        pass

    @abc.abstractmethod
    async def _connect(self):
        pass

    async def _reconnect(self):
        await self._disconnect()

        while True:
            try:
                await self._connect()
                return
            except (OSError, RuntimeError):
                await asyncio.sleep(self._retry_timeout)

    async def exit(self):
        await self._queue.join()

        for consumer in self._consumers:
            consumer.cancel()

        await self._disconnect()


class TCPHandler(BaseHandler):

    def __init__(self):
        super().__init__()
        self._writer = None

    async def connect(self, host, port):
        self._host = host
        self._port = port
        await self._connect()

    async def _connect(self):
        _, self._writer = await asyncio.open_connection(
            host=self._host,
            port=self._port
        )

    async def _send(self, data):
        self._writer.write(data)

        await self._writer.drain()

    async def _disconnect(self):
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None

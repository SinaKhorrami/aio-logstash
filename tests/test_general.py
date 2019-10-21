import aio_logstash
import socket
import sys
import pytest
from unittest import mock


@pytest.mark.asyncio
async def test_logger(make_logger):
    logger, handler, server = await make_logger()
    logger.info('test', extra={'foo': 'bar'})

    log = await server.get_data()

    assert log == {
        "@version": "1",
        "type": "aio_logstash",
        "message": "test",
        "logger_name": "aio-logstash_test",
        "level": "INFO",
        "host": socket.gethostname(),
        "interpreter": sys.executable,
        "interpreter_version": '{major}.{minor}.{micro}'.format(
            major=sys.version_info.major,
            minor=sys.version_info.minor,
            micro=sys.version_info.micro
        ),
        "program": sys.argv[0],
        "aio_logstash_version": aio_logstash.__version__,
        "path": __file__,
        "@timestamp": mock.ANY,
        "pid": mock.ANY,
        "func_name": mock.ANY,
        "line": mock.ANY,
        "thread_name": mock.ANY,
        "process_name": mock.ANY,
        "stack_trace": None,
        "extra": {
            "foo": "bar",
            "message": "test"
        }
    }

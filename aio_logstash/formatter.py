import abc
import json
import logging
import socket
import sys
import time
import aio_logstash
import traceback
from aio_logstash import constants
from datetime import datetime, date


class BaseFormatter(logging.Formatter):

    def __init__(self, message_type='aio_logstash', fqdn=False):
        super().__init__()

        self._message_type = message_type
        self._host = socket.getfqdn() if fqdn else socket.gethostname()
        self._interpreter = sys.executable
        self._interpreter_vesion = '{major}.{minor}.{micro}'.format(
            major=sys.version_info.major,
            minor=sys.version_info.minor,
            micro=sys.version_info.micro
        )
        self._program_name = sys.argv[0]

    @staticmethod
    def _format_timestamp(_time):
        tstamp = datetime.utcfromtimestamp(_time)

        return tstamp.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (tstamp.microsecond / 1000) + "Z"

    @staticmethod
    def _format_stack_trace(exc_info):
        if exc_info:
            return ''.join(traceback.format_exception(*exc_info))

        return None

    @staticmethod
    def _serialize(message):
        return bytes(json.dumps(message), encoding='utf-8')

    @abc.abstractmethod
    def format(self, record):
        pass

    def _get_base_fields(self):
        base_fields = {
            'host': self._host,
            'type': self._message_type,
            'interpreter': self._interpreter,
            'interpreter_version': self._interpreter_vesion,
            'program': self._program_name,
            'aio_logstash_version': aio_logstash.__version__,
        }

        return base_fields

    def _get_record_fields(self, record):
        record_fields = {
            'message': record.getMessage(),
            'pid': record.process,
            'func_name': record.funcName,
            'line': record.lineno,
            'logger_name': record.name,
            'path': record.pathname,
            'thread_name': record.threadName,
            'level': record.levelname,
            'process_name': record.processName,
            'stack_trace': self._format_stack_trace(record.exc_info)
        }

        return record_fields

    def _get_extra_fields(self, record):
        extra_fields = dict()

        for k, v in record.__dict__.items():
            if k not in constants.LOG_RECORD_DEFAULT_ATTRIBUTES:
                extra_fields[k] = self._get_value_repr(v)

        return extra_fields

    def _get_value_repr(self, value):
        easy_types = (bool, float, type(None), str, int)

        if isinstance(value, dict):
            return {k: self._get_value_repr(v) for k, v in value.items()}
        elif isinstance(value, (tuple, list)):
            return [self._get_value_repr(v) for v in value]
        elif isinstance(value, (datetime, date)):
            return self._format_timestamp(time.mktime(value.timetuple()))
        elif isinstance(value, easy_types):
            return value
        else:
            return repr(value)


class V1Formatter(BaseFormatter):

    def format(self, record):
        message = {
            '@timestamp': self._format_timestamp(record.created),
            '@version': '1'
        }

        base_fields = self._get_base_fields()
        message.update(base_fields)

        record_fields = self._get_record_fields(record)
        message.update(record_fields)

        extra_fields = self._get_extra_fields(record)
        message.update({
            'extra': extra_fields
        })

        return self._serialize(message)

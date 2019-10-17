import http
from typing import Optional

import six

from ansib.server.common.config import CONF


class APIException(Exception):
    """
    Base API error class.

    Child classes can define an HTTP status code and/or message.
    """

    host = 'localhost'
    code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    message = "An unknown exception occurred."
    exception = None  # type: Optional[Exception]

    def __init__(self, message=None, exception=None, **kwargs):

        if CONF.ansible.host:
            self.host = CONF.ansible.host

        if message:
            self.message = message

        if exception:
            self.exception = exception

        print(kwargs)
        try:
            self.msg = self.message % kwargs
        except Exception:
            self.msg = self.message

        super(APIException, self).__init__(self.msg)

    def __unicode__(self):
        return six.text_type(self.msg)

    def json_encode(self):
        res = {
            self.host: {
                'exception': '',
                'msg': "%s -> %s" % (
                    self.__class__.__name__,
                    str(self.msg),
                ),
                'stdout': '',
                '_ansible_no_log': False
            }
        }
        if self.exception is not None:
            res[self.host]['exception'] = "%s -> %s" % (
                self.exception.__class__.__name__,
                str(self.exception),
            )
        return res


class NotFound(APIException):
    code = http.HTTPStatus.NOT_FOUND
    message = "%(resource)s %(id)s not found."


class ValidationException(APIException):
    code = http.HTTPStatus.BAD_REQUEST
    message = "Validation failure: %(detail)s"


class SaveFileException(APIException):
    code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    message = "Save file failure: %(detail)s"


class RemoveFileException(APIException):
    code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    message = "Remove file failure: %(detail)s"

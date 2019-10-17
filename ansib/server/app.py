import http
import json
import logging
import os
import socket
import sys

import flask
import yaml
from flask import Flask

from ansib.server.api import v1 as api_v1
from ansib.server.common import config, context
from ansib.server.common import constants
from ansib.server.common import exceptions
from ansib.server.common.config import CONF
from ansib.server.common.exceptions import APIException

LOG = logging.getLogger(__name__)


def create_app(config_path=None):
    if config_path is None:
        config_path = '/etc/ansib/server/config.yaml'

    app = Flask(__name__)
    try:
        LOG.debug('Initialize config')
        config.init_app(config_path)
    except Exception as e:
        LOG.fatal("Unsupported configuration file: ", e)
        raise e

    log_level = logging.NOTSET
    if CONF.log_level == 'CRITICAL':
        log_level = logging.CRITICAL
    elif CONF.log_level == 'FATAL':
        log_level = logging.CRITICAL
    elif CONF.log_level == 'ERROR':
        log_level = logging.ERROR
    elif CONF.log_level == 'WARNING':
        log_level = logging.WARNING
    elif CONF.log_level == 'WARN':
        log_level = logging.WARNING
    elif CONF.log_level == 'INFO':
        log_level = logging.INFO
    elif CONF.log_level == 'DEBUG':
        log_level = logging.DEBUG

    init_logging(
        log_dir=None,
        log_level=log_level,
    )
    LOG.debug('Flask version: {}'.format(flask.__version__))
    LOG.debug('Hostname: %s' % (socket.gethostname()))

    # We use our own format for error messages.
    app.config.update(ERROR_INCLUDE_MESSAGE=False)
    # Flask-RESTPlus options
    app.config.update(RESTPLUS_MASK_SWAGGER=False)
    app.config.update(RESTPLUS_VALIDATE=True)

    LOG.debug('Initialize Blueprints')

    api_v1.api.representation(constants.APPLICATION_JSON)(_json_response)
    api_v1.api.errorhandler(exceptions.APIException)(_handle_exception)

    api_v1_blueprint = flask.Blueprint('/api/v1', __name__)
    api_v1.api.init_app(api_v1_blueprint)
    app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')

    app.wsgi_app = context.ContextMiddleware(app.wsgi_app)

    LOG.debug('Supported Methods:')
    for rule in app.url_map.iter_rules():
        for method in rule.methods:
            if method != 'OPTIONS':
                LOG.debug("PATH: %s \t\t %s" % (method, rule))
            else:
                LOG.debug("PATH: %s \t %s" % (method, rule))

    return app


# if __name__ == '__main__':
# config_path = os.environ['CONFIG_PATH'] or '/etc/ansib/server/config.yaml'
# create_app(config_path)


def init_logging(log_dir=None, log_level=logging.DEBUG):
    """Setup Google-Style logging for the entire application.
    At first I hated this but I had to use it for work, and now I prefer it.
    Who knew?
    From: https://github.com/twitter/commons/blob/master/src/python/twitter/
    common/log/formatters/glog.py
    Always logs DEBUG statements somewhere.
    """
    log_to_disk = False
    if type(log_dir) == str:
        if not os.path.isdir(log_dir):
            print(
                'ERROR: Directory {} does not exist.'.format(log_dir)
            )
            sys.exit(1)
        if not os.access(log_dir, os.W_OK):
            print(
                'ERROR: No permissions to write to '
                'directory {}.'.format(log_dir)
            )
            sys.exit(1)
        log_to_disk = True

    fmt = '%(levelletter)s%(asctime)s.%(msecs).03d %(process)d %(filename)s:' \
          '%(lineno)d] %(message)s'
    datefmt = '%m%d %H:%M:%S'
    formatter = CustomFormatter(fmt, datefmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR if log_to_disk else logging.DEBUG)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(console_handler)

    if log_to_disk:
        file_name = os.path.join(log_dir, 'agent.log')
        file_handler = logging.handlers.TimedRotatingFileHandler(
            file_name,
            when='d',
            backupCount=7,
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


class CustomFormatter(logging.Formatter):
    LEVEL_MAP = {
        logging.FATAL: 'F',
        logging.ERROR: 'E',
        logging.WARN: 'W',
        logging.INFO: 'I',
        logging.DEBUG: 'D',
    }

    def format(self, record):
        record.levelletter = self.LEVEL_MAP[record.levelno]
        return super(CustomFormatter, self).format(record)


def _json_response(data, code, headers=None):
    """Make a Flask response with a JSON encoded body."""
    headers = headers or {}
    if isinstance(data, APIException):
        dumped = json.dumps(data.json_encode())
        resp = flask.make_response(dumped, data.code)
    elif data is not None:
        dumped = json.dumps(data)
        resp = flask.make_response(dumped, code)
    else:
        resp = flask.make_response('', http.HTTPStatus.NO_CONTENT)
        headers['Content-Length'] = 0
    resp.headers.extend(headers)
    return resp


def _yaml_response(data, code, headers=None):
    """Make a Flask response with a YAML encoded body."""
    headers = headers or {}
    if data is not None:
        dumped = yaml.dump(data)
        resp = flask.make_response(dumped, code)
    else:
        resp = flask.make_response('', http.HTTPStatus.NO_CONTENT)
        headers['Content-Length'] = 0
    resp.headers.extend(headers)
    return resp


def _handle_exception(ex):
    error_data = {
        'code': ex.code,
        'title': http.client.responses.get(ex.code) or '',
        'message': str(ex),
    }
    return error_data, http.HTTPStatus.BAD_REQUEST

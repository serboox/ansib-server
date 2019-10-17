#!/usr/bin/env python3
"""
Command details:
    server                      Run the application using the WSGI Development
Usage:
    agent.py server [--host IP] [--port NUM] [--config PATH] [--debug]
    agent.py (-h | --help)
Options:
    --host IP                   Flask will take on this IP.
                                [default: 127.0.0.1]
    --port NUM                  Flask will listen on this port number.
                                [default: 5000]
    --config PATH               Path to configuration file.
                                [default: /etc/ansib/server/config.yaml]
"""

import logging
import sys
from wsgiref import simple_server

from docopt import docopt

from ansib.server import app as api_app

LOG = logging.getLogger(__name__)
OPTIONS = docopt(__doc__) if __name__ == '__main__' else dict()


def main():

    app = api_app.create_app(config_path=OPTIONS['--config'])

    host = OPTIONS['--host']
    port = int(OPTIONS['--port'])
    LOG.info('Starting API server on %(host)s:%(port)s',
             {'host': host, 'port': port})
    server = simple_server.make_server(host, port, app)
    server.serve_forever()


if __name__ == "__main__":
    OPTIONS.setdefault('--host', '127.0.0.1')
    OPTIONS.setdefault('--port', 5001)
    OPTIONS.setdefault('--config', '/etc/ansib/server/config.yaml')
    sys.exit(main())

#!/usr/bin/env python3
"""
Command details:
    devserver           Run the application using the Flask Development
Usage:
    manage.py server [--host IP] [--port NUM] [--config PATH] [--debug]
        [-l DIR]
    manage.py (-h | --help)
Options:
    --host IP                   Flask will take on this IP.
                                [default: 127.0.0.1]
    --port NUM                  Flask will listen on this port number.
                                [default: 5000]
    --debug                     Flask will be run debug mode
                                [default: False]
    --config PATH               Path to configuration file.
                                [default: /etc/ansib/server/config.yaml]
    -l DIR --log_dir=DIR        Log all statements to file in this directory
                                instead of stdout.
                                Only ERROR statements will go to stdout. stderr
                                is not used.
"""

import logging
import signal
import sys
from functools import wraps

from docopt import docopt

from ansib.server.app import create_app

LOG = logging.getLogger(__name__)
OPTIONS = docopt(__doc__) if __name__ == '__main__' else dict()


def command(func):
    """Decorator that registers the chosen command/function."""

    @wraps(func)
    def wrapped():
        return func()

    # Register chosen function.
    if func.__name__ not in OPTIONS:
        raise KeyError(
            'Cannot register {}, not mentioned in '
            'docstring/docopt.'.format(func.__name__))
    if OPTIONS[func.__name__]:
        print("Current: {}".format(func.__name__))
        command.chosen = func


@command
def server():
    app = create_app(OPTIONS['--config'])
    app.run(
        host=OPTIONS['--host'],
        port=int(OPTIONS['--port']),
        debug=bool(OPTIONS['--debug']),
    )


if __name__ == '__main__':
    # Properly handle Control+C
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

    if '--port' in OPTIONS.keys() and not OPTIONS['--port'].isdigit():
        print('ERROR: Port should be a number.')
        sys.exit(1)

    OPTIONS.setdefault('--host', '127.0.0.1')
    OPTIONS.setdefault('--port', 5000)
    OPTIONS.setdefault('--debug', False)
    OPTIONS.setdefault('--config', '/etc/ansib/server/config.yaml')

    # Execute the function specified by the user.
    sys.exit(getattr(command, 'chosen')())

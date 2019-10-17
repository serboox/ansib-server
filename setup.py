# THIS FILE IS MANAGED BY THE GLOBAL REQUIREMENTS REPO - DO NOT EDIT
from __future__ import print_function

import os
import warnings

from setuptools.command.install import install
from setuptools import setup, find_packages

# sys.path.insert(0, os.path.abspath('ansib-server'))
from ansib.server.release import __version__, __author__

PYCRYPTO_DIST = 'pycrypto'


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        pass


def read_file(file_name):
    """Read file and return its contents."""
    with open(file_name, 'r') as f:
        return f.read()


def read_requirements(file_name):
    """Read requirements file as a list."""
    reqs = read_file(file_name).splitlines()
    if not reqs:
        raise RuntimeError(
            "Unable to read requirements from the %s file"
            "That indicates this copy of the source code is incomplete."
            % file_name
        )
    return reqs


def get_crypto_req():
    """Detect custom crypto from AGENT_CRYPTO_BACKEND env var.

    pycrypto or cryptography. We choose a default but allow the user to
    override it. This translates into pip install of the sdist deciding what
    package to install and also the runtime dependencies that pkg_resources
    knows about.
    """
    crypto_backend = os.environ.get('AGENT_CRYPTO_BACKEND', '').strip()

    if crypto_backend == PYCRYPTO_DIST:
        # Attempt to set version requirements
        return '%s >= 2.6' % PYCRYPTO_DIST

    return crypto_backend or None


def substitute_crypto_to_req(req):
    """Replace crypto requirements if customized."""
    crypto_backend = get_crypto_req()

    if crypto_backend is None:
        return req

    def is_not_crypto(r):
        CRYPTO_LIBS = PYCRYPTO_DIST, 'cryptography'
        return not any(r.lower().startswith(c) for c in CRYPTO_LIBS)

    return [r for r in req if is_not_crypto(r)] + [crypto_backend]


def get_dynamic_setup_params():
    """Add dynamically calculated setup params to static ones."""
    return {
        # Retrieve the long description from the README
        'long_description': read_file('README.md'),
        'install_requires': substitute_crypto_to_req(
            read_requirements('requirements.txt'),
        ),
    }


static_setup_params = dict(
    name='ansib.server',
    version=__version__,
    description='Radically simple IT automation',
    author=__author__,
    author_email='serboox@gmail.com',
    url='https://github.com/serboox/ansib-server',
    license='GPLv3+',
    # package_dir={'server': 'ansib/server'},
    # package_dir={'': 'ansib'},
    # packages=find_packages('ansib.server'),
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console :: Web',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License '
        'v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    scripts=[],
    data_files=[],
    # Installing as zip files would break due to references to __file__
    zip_safe=False,
    # The several automatisation responsibilities
    # setup_requires=['pbr>=2.0.0'],
    # pbr=True
)


def main():
    """Invoke installation process using setuptools."""
    setup_params = dict(static_setup_params, **get_dynamic_setup_params())
    ignore_warning_regex = (
        r"Unknown distribution option: '(project_urls|python_requires)'"
    )
    warnings.filterwarnings(
        'ignore',
        message=ignore_warning_regex,
        category=UserWarning,
        module='distutils.dist',
    )
    setup(**setup_params)
    warnings.resetwarnings()


if __name__ == '__main__':
    main()

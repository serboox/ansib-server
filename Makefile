# WARN: gmake syntax
########################################################
# Makefile for Ansible Server
#
# useful targets:
#   make run-r ---------------- run application in develop virtual mashine
#   make deb ------------------ produce a DEB

########################################################
# variable section

APP?=server
NAME:=ansib-server
OS = $(shell uname -s)
USERSPACE?=serboox
RELEASE?=0.0.1
PROJECT?=github.com/${USERSPACE}/${APP}
BUILD_TIME?=$(shell date -u '+%Y-%m-%d_%H:%M:%S')
OS?=linux
REMOTE_USER?=root
REMOTE_HOST?=$(shell echo $$DEVELOP_HOST)

PWD?=$(shell echo $PWD)
CONFIG_PATH?=${PWD}/config.yaml

PYTHON3=$(shell which python3)
PYTHON2=$(shell which python2)
PYTHON?=${PYTHON3}
VIRTUAL_ENV=${NAME}

# fetch version from project release.py as single source-of-truth
VERSION := $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --raw || echo error)
ifeq ($(findstring error,$(VERSION)), error)
	$(error "version_helper failed")
endif

MAJOR_VERSION := $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --majorversion)
CODENAME := $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --codename)

# if a specific release was not requested, set to 1 (RPMs have "fancier" logic for this further down)
RELEASE ?= 1.0.0

# Get the branch information from git
ifneq ($(shell which git),)
	GIT_DATE := $(shell git log -n 1 --format="%ci")
	GIT_HASH := $(shell git log -n 1 --format="%h")
	GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD | sed 's/[-_.\/]//g')
	GITINFO = .$(GIT_HASH).$(GIT_BRANCH)
	REPO_INFO=$(shell git config --get remote.origin.url)
else
	GITINFO = ""
endif

ifeq ($(shell echo $(OS) | egrep -c 'Darwin|FreeBSD|OpenBSD|DragonFly'),1)
	DATE := $(shell date -j -r $(shell git log -n 1 --format="%ct") +%Y%m%d%H%M)
	CPUS ?= $(shell sysctl hw.ncpu|awk '{print $$2}')
else
	DATE := $(shell date --utc --date="$(GIT_DATE)" +%Y%m%d%H%M)
	CPUS ?= $(shell nproc)
endif

# DEB build parameters
DEBUILD_BIN ?= debuild
DEBUILD_OPTS = --source-option="-I"
DPUT_BIN ?= dput
DPUT_OPTS ?=
DEB_DATE := $(shell LC_TIME=C date +"%a, %d %b %Y %T %z")
DEB_VERSION ?= $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --debversion)
ifeq ($(OFFICIAL),yes)
    DEB_RELEASE ?= $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --debrelease)ppa
    # Sign OFFICIAL builds using 'DEBSIGN_KEYID'
    # DEBSIGN_KEYID is required when signing
    ifneq ($(DEBSIGN_KEYID),)
        DEBUILD_OPTS += -k$(DEBSIGN_KEYID)
    endif
else
    DEB_RELEASE ?= 100.git$(DATE)$(GITINFO)
    # Do not sign unofficial builds
    DEBUILD_OPTS += -uc -us
    DPUT_OPTS += -u
endif
DEBUILD = $(DEBUILD_BIN) $(DEBUILD_OPTS)
DEB_PPA ?= ppa
# Choose the desired Ubuntu release: lucid precise saucy trusty unstable
DEB_DIST ?= unstable

# pbuilder parameters
PBUILDER_ARCH ?= amd64
PBUILDER_CACHE_DIR = /var/cache/pbuilder
PBUILDER_BIN ?= pbuilder
PBUILDER_OPTS ?= --debootstrapopts --variant=buildd --architecture $(PBUILDER_ARCH) --debbuildopts -b

# Get gunicorn settings
DAEMON_ARGS?=

HOST?=0.0.0.0
PORT?=5007
GUNICORN_BIND?="${HOST}:${PORT}"
GUNICORN_BACKLOG?=1024
GUNICORN_WORKERS?=1
GUNICORN_THREADS?=4
GUNICORN_WORKER_CLASS?=gthread
GUNICORN_MAX_REQUESTS?=1
GUNICORN_MAX_REQUESTS_JITTER?=100

ANSIBLE_SERVER_APP?=ansib.server.app:create_app('${CONFIG_PATH}')

default_target: run-r

.PHONY: run
run:
	@echo "+ $@"
	mkdir -p /var/run/ansib-server
	gunicorn ${DAEMON_ARGS} \
    --pid /var/run/ansib/server.pid \
    --bind ${GUNICORN_BIND} \
    --backlog ${GUNICORN_BACKLOG} \
    --workers ${GUNICORN_WORKERS} \
    --threads ${GUNICORN_THREADS} \
    --worker-class ${GUNICORN_WORKER_CLASS} \
    --max-requests ${GUNICORN_MAX_REQUESTS} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER} \
    --name ansib-server \
    --log-level DEBUG \
    --log-syslog \
    "${ANSIBLE_SERVER_APP}"

.PHONY: run-wsgiref
run-wsgiref: install-in-environments
	@echo "+ $@"
	python ./ansib/server/cmd/agent.py server --host ${HOST} \
	--port ${PORT} \
	--config ${CONFIG_PATH}

.PHONY: run-manage
run-manage:
	@echo "+ $@"
	./manage.py server \
	--config config.yaml \
	--host ${HOST} \
	--port ${PORT} \
	--debug

.PHONY: run-flask
run-flask:
	@echo "+ $@"
	env FLASK_ENV=development \
	FLASK_DEBUG=0 \
	FLASK_APP="./ansib/server/app.py:create_app('${CONFIG_PATH}')" \
	flask run --host ${HOST} --port ${PORT}

.PHONY: kill-r
kill-r:
	@echo "+ $@"
	lsof -i tcp:${PORT} | grep TCP | awk '{print $$2}' | xargs -I {} kill -9 {}
	# ps aux | grep agent.py | grep -v /bin/sh | grep -v grep | \
	# awk '{print $$2}' | xargs -I {} kill -9 {}

.PHONY: run-r
run-r: flake8 rsync kill-r
	@echo "+ $@"
	ssh -t -A ${REMOTE_USER}@${REMOTE_HOST} /bin/bash \
	-c "pwd >> /dev/null && cd ~/python/${PROJECT} \
	&& exec bash -ci 'workon ${VIRTUAL_ENV} && make run'"

.PHONY: install-in-environments
install-in-environments:
	@echo "+ $@"
	pip install -e . > /dev/null

# Tests
.PHONY: flake8
flake8:
	@echo "+ $@"
	python -m flake8 ./ansible

# PIP commands
.PHONY: pip-freeze
pip-freeze:
	@echo "+ $@"
	pip freeze > requirements.txt

.PHONY: pip-install
pip-install:
	@echo "+ $@"
	pip install -r requirements.txt

.PHONY: pip-uninstall-all
pip-uninstall-all:
	@echo "+ $@"
	pip freeze | xargs -I {} pip uninstall -y {}

# Docker commands
.PHONY: docker-build
docker-build:
	@echo "+ $@"
	# docker build -t ansib-${APP}:latest . --no-cache --force-rm
	docker build -t ansib-${APP}:latest .

.PHONY: docker-run
docker-run:
	@echo "+ $@"
	mkdir -p ./tmp
	cp ./config.yaml ./tmp/config.yaml
	docker run --rm --name ansib-${APP} -v $(CURDIR)/tmp:/etc/ansib/${APP} -p ${PORT}:${PORT} ansib-${APP}:latest

.PHONY: docker-rmi
docker-rmi:
	@echo "+ $@"
	docker rmi -f $$(docker images | grep none | awk '{print $$3}')

.PHONY: docker-br
docker-br: docker-build docker-run
	@echo "+ $@"

# Other
.PHONY: rsync
rsync:
	@echo "+ $@"
	rsync --delete --recursive -avzhe ssh --progress . ${REMOTE_USER}@${REMOTE_HOST}:/${REMOTE_USER}/python/${PROJECT}

.PHONY: init-wirtualenvwrapper
init-wirtualenvwrapper:
	@echo "+ $@"
	mkvirtualenv --python=/usr/bin/python3 ${VIRTUAL_ENV}

.PHONY: deb
deb:
	@echo "+ $@"
	docker build -t ${NAME}:latest --file ./debian/Dockerfile .



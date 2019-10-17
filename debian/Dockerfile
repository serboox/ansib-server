FROM ubuntu:18.04 as builder

ENV APP_NAME=ansib-server
ENV HOME=/root
ENV PL_NAME=python
ENV GITHUB_DOMAIN=github.com
ENV GITHUB_PR_GROUP=serboox
ENV GITHUB_PR_NAME=ansib-server
ENV PROJECT_PATH=$HOME/$PL_NAME/$GITHUB_DOMAIN/$GITHUB_PR_GROUP/$GITHUB_PR_NAME
ENV DEB_PATH=$HOME/$PL_NAME/$GITHUB_DOMAIN/$GITHUB_PR_GROUP
ENV DOWNLOADS_PATH=$HOME/Downloads

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR $PROJECT_PATH

RUN apt-get update && apt-get install -y \
    cdbs \
    debootstrap \
    devscripts \
    make \
    pbuilder \
    debhelper \
    dh-python \
    dh-virtualenv \
    dh-systemd \
    python3-all \
    python3-pip \
    python3-setuptools \
    python3-pbr \
    python3-crypto \
    python3-docutils \
    python3-jinja2 \
    python3-nose \
    python3-packaging \
    python3-passlib \
    python3-setuptools \
    python3-yaml \
    python3-cryptography \
    python3-jmespath \
    python3-kerberos \
    python3-libcloud \
    python3-selinux \
    python3-winrm \
    python3-xmltodict \
    python3-flask \
    python3-aniso8601 \
    python3-gunicorn \
    && apt-get clean \
    && python3 -m pip install --upgrade pip

COPY . $PROJECT_PATH

RUN dpkg-buildpackage -rfakeroot -D -us -uc -b \
    && mkdir -p $DOWNLOADS_PATH \
    && mv $DEB_PATH/*.deb $DOWNLOADS_PATH/

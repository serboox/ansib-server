FROM ubuntu:18.04 as builder
LABEL MANTAINER="Sergei Bukharkin <serboox@gmail.com>"

ENV APP_NAME=ansib-server
ENV HOME=/root
ENV GITHUB_DOMAIN=github.com
ENV GITHUB_PROJECT_GROUP=serboox
ENV GITHUB_PROJECT_NAME=ansib-server
ENV WORKDIR_PATH=$HOME/python/$GITHUB_DOMAIN/$GITHUB_PROJECT_GROUP/$GITHUB_PROJECT_NAME

ENV WORKON_HOME=$HOME/.virtualenvs
ENV PROJECT_HOME=$HOME/python/$GITHUB_DOMAIN/$GITHUB_PROJECT_GROUP/$GITHUB_PROJECT_NAME
ENV VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
ENV VIRTUALENVWRAPPER_SCRIPT=/usr/local/bin/virtualenvwrapper.sh
ENV APP_CONFIG_PATH=/etc/ansib/server/config.yaml

RUN apt-get update -y && apt-get install -y \
    make \
    curl \
    git \
    vim \
    ca-certificates \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p $WORKDIR_PATH
COPY ./requirements.txt $WORKDIR_PATH/requirements.txt
WORKDIR $WORKDIR_PATH
RUN python3 -m pip install virtualenvwrapper
RUN echo 'source $VIRTUALENVWRAPPER_SCRIPT' >> /etc/bash.bashrc
RUN /bin/bash --login -c 'source $VIRTUALENVWRAPPER_SCRIPT && \
        mkvirtualenv $APP_NAME'
RUN /bin/bash --login -c 'python3 -m pip install -r requirements.txt'

COPY config.example.yaml $APP_CONFIG_APTH
COPY . $WORKDIR_PATH

RUN echo 'CONFIG_PATH=${APP_CONFIG_PATH} make run' > run.sh && \
    mkdir -p /var/run/ansib

EXPOSE 5007
CMD /bin/bash ./run.sh

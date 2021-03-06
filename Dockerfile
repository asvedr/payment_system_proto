FROM ubuntu:18.04

ARG MODE=develop
ENV DOCKER_MODE=$MODE

# Copy data
COPY deps /deps
RUN apt-get update
RUN apt-get install gpg -y
RUN apt-key add /deps/pg.asc
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" >> /etc/apt/sources.list.d/pgdg.list
COPY entrypoint.sh /entrypoint.sh
COPY test_entrypoint.sh /test_entrypoint.sh

RUN apt-get update

# Patch ubuntu for Russia
RUN apt install -y locales
RUN locale-gen ru_RU.UTF-8
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Install all deps
RUN apt-get install wget curl gnupg -y
RUN wget -O - "https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey" | apt-key add -
RUN cat /deps/ubuntu.txt | xargs apt-get install -y
RUN pip3 install -r /deps/python.txt
RUN rm -r /deps

CMD /bin/bash entrypoint.sh

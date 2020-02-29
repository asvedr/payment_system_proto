FROM ubuntu:18.04

ARG MODE=develop
ENV DOCKER_MODE=$MODE

# Copy data
COPY deps /deps
COPY src /src
COPY entrypoint.sh /entrypoint.sh
COPY test_entrypoint.sh /test_entrypoint.sh

RUN if [ "$MODE" = "develop" ] ; then rm -r /src; mv /test_entrypoint.sh /entrypoint.sh; else rm /test_entrypoint.sh; fi

RUN apt-get update

# Patch ubuntu for Russia
RUN apt install -y locales
RUN locale-gen ru_RU.UTF-8
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Install all deps
RUN cat /deps/ubuntu.txt | xargs apt-get install -y
RUN pip3 install -r /deps/python.txt
RUN rm -r /deps

CMD /bin/bash entrypoint.sh

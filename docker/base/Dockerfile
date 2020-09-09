FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get -y install \
    python3 \
    python3-dev \
    python3-pip \
    python-is-python3 \
 && rm -rf /var/cache/apt/*

## Python packages
COPY requirements.txt /opt/requirements.txt
RUN pip3 install --no-binary annoylib -r /opt/requirements.txt \
 && rm -rf /root/.cache/pip

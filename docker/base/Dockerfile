FROM pypy:3

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get -y install \
    libmemcached-dev \
    python3 \
    python3-dev \
    python3-pip \
 && rm -rf /var/cache/apt/*

## Python packages
COPY requirements.txt /opt/requirements.txt
RUN pip3 install --no-binary annoylib -r /opt/requirements.txt \
 && rm -rf /root/.cache/pip

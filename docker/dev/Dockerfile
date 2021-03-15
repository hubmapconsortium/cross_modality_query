FROM hubmap/cross-modality-query-base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get -y install \
    vim \
 && rm -rf /var/cache/apt/*

## Python packages
COPY requirements-dev.txt /opt/requirements-dev.txt
RUN python3 -m pip install -r /opt/requirements-dev.txt \
 && rm -rf /root/.cache/pip

ENV DJANGO_SETTINGS_MODULE=hubmap_query.settings
ENV PYTHONPATH=/code

FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get -y install \
    libmemcached-dev \
    python3 \
    python3-dev \
    python3-pip \
    python-is-python3 \
 && rm -rf /var/cache/apt/*

## Python packages
COPY requirements.txt /opt/requirements.txt
COPY data /opt

WORKDIR /opt

RUN pip3 install --no-binary annoylib -r /opt/requirements.txt \
 && rm -rf /root/.cache/pip

RUN mkdir -p /opt/data/zarr/example.zarr

RUN curl https://s3.amazonaws.com/cells-api-index-assets/rna.hdf5 --output /opt/rna.hdf5
RUN curl https://s3.amazonaws.com/cells-api-index-assets/rna.h5ad --output /opt/rna.h5ad
RUN curl https://s3.amazonaws.com/cells-api-index-assets/rna_precompute.hdf5 --output /opt/rna_precompute.hdf5
RUN curl https://s3.amazonaws.com/cells-api-index-assets/atac.hdf5 --output /opt/atac.hdf5
RUN curl https://s3.amazonaws.com/cells-api-index-assets/atac.h5ad --output /opt/atac.h5ad
RUN curl https://s3.amazonaws.com/cells-api-index-assets/atac_precompute.hdf5 --output /opt/atac_precompute.hdf5
RUN curl https://s3.amazonaws.com/cells-api-index-assets/codex.hdf5 --output /opt/codex.hdf5
RUN curl https://s3.amazonaws.com/cells-api-index-assets/codex.h5ad --output /opt/codex.h5ad
RUN curl https://s3.amazonaws.com/cells-api-index-assets/codex_precompute.hdf5 --output /opt/codex_precompute.hdf5

WORKDIR /opt/data/zarr/example.zarr

RUN curl https://s3.amazonaws.com/cells-api-index-assets/codex.tar.gz | tar -xzf -
RUN curl https://s3.amazonaws.com/cells-api-index-assets/rna.tar.gz | tar -xzf -
RUN curl https://s3.amazonaws.com/cells-api-index-assets/atac.tar.gz | tar -xzf -
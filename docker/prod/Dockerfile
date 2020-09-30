FROM hubmap/cross-modality-query-base:latest

RUN apt-get update \
 && apt-get -y install \
    uwsgi \
    uwsgi-plugin-python3 \
 && rm -rf /var/cache/apt/*

COPY . /opt/cross-modality-query

WORKDIR /opt/cross-modality-query
RUN mv hubmap_query/production_settings.py hubmap_query/local_settings.py
RUN python3 -m compileall .
RUN python3 -O -m compileall .

VOLUME /opt/secret

EXPOSE 8000

ENTRYPOINT ["uwsgi", "--xml", "/opt/cross-modality-query/uwsgi/uwsgi.xml"]

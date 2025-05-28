ARG VERSION=latest

FROM ghcr.io/esphome/esphome:${VERSION}

ENV PLATFORMIO_GLOBALLIB_DIR=

COPY entrypoint.py /entrypoint.py

RUN chmod 755 /entrypoint.py

ENTRYPOINT ["/entrypoint.py"]

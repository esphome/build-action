ARG VERSION=latest

FROM ghcr.io/esphome/esphome:${VERSION}

COPY entrypoint.py /entrypoint.py

ENTRYPOINT ["/entrypoint.py"]

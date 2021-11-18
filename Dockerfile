FROM ghcr.io/esphome/esphome:latest

COPY rootfs /

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

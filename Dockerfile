FROM ghcr.io/esphome/esphome:latest

COPY entrypoint.py /entrypoint.py

ENTRYPOINT ["/entrypoint.py"]

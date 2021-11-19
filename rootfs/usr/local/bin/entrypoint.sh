#!/bin/bash

set -e

esphome compile $1

version$(esphome version | cut -d' ' -f2)
echo "::set-output name=esphome-version::$version"

exec /usr/local/bin/get_flash_images.py $1

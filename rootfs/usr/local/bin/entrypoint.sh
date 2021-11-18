#!/bin/bash

set -e

esphome compile $1

exec /usr/local/bin/get_flash_images.py $1 $2

#!/usr/bin/python3

import os
import subprocess
import sys
import json
import shutil
from pathlib import Path
import re
import yaml

GH_RUNNER_USER_UID = 1001
GH_RUNNER_USER_GID = 121

ESP32_CHIP_FAMILIES = {
    "ESP32": "ESP32",
    "ESP32S2": "ESP32-S2",
    "ESP32S3": "ESP32-S3",
    "ESP32C3": "ESP32-C3",
}

if len(sys.argv) != 2:
    print("Usage: entrypoint.py <image_file>")
    sys.exit(1)

filename = Path(sys.argv[1])

print("::group::Compile firmware")
rc = subprocess.run(["esphome", "compile", filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
if rc.returncode != 0:
    sys.exit(rc)

print(rc.stdout.decode("utf-8"))
print("::endgroup::")

print("::group::Get ESPHome version")
try:
    version = subprocess.check_output(["esphome", "version"])
except subprocess.CalledProcessError as e:
    sys.exit(e.returncode)
version = version.decode("utf-8")
print(version)
version = version.split(" ")[1]
print(f"::set-output name=esphome-version::{version}")
print("::endgroup::")

print("::group::Get config")
try:
    config = subprocess.check_output(["esphome", "config", filename], stderr=sys.stderr)
except subprocess.CalledProcessError as e:
    sys.exit(e.returncode)

config = config.decode("utf-8")
print(config)

yaml.add_multi_constructor("", lambda _, t, n: t + " " + n.value)
config = yaml.load(config, Loader=yaml.FullLoader)

name = config["esphome"]["name"]

platform = ""
if "esp32" in config:
    platform = "esp32"
elif "esp8266" in config:
    platform = "esp8266"

name += f"-{platform}"

print(f"::set-output name=name::{name}")
print("::endgroup::")

file_base = Path(name)

print("::group::Get IDEData")
try:
    idedata = subprocess.check_output(["esphome", "idedata", filename], stderr=sys.stderr)
except subprocess.CalledProcessError as e:
    sys.exit(e.returncode)

data = json.loads(idedata.decode("utf-8"))
print(json.dumps(data, indent=2))

elf = Path(data["prog_path"])
bin = elf.with_name("firmware-factory.bin")
print("::endgroup::")

print("::group::Copy firmware file(s) to folder")
file_base.mkdir(parents=True, exist_ok=True)

if os.environ.get("GITHUB_JOB") is not None:
    shutil.chown(file_base, GH_RUNNER_USER_UID, GH_RUNNER_USER_GID)

shutil.copyfile(bin, file_base / f"{name}.bin")
if os.environ.get("GITHUB_JOB") is not None:
    shutil.chown(file_base / f"{name}.bin", GH_RUNNER_USER_UID, GH_RUNNER_USER_GID)

print("::endgroup::")

print("::group::Write manifest.json file")

chip_family = None
define: str
for define in data["defines"]:
    if define == "USE_ESP8266":
        chip_family = "ESP8266"
        break
    elif m := re.match(r"USE_ESP32_VARIANT_(\w+)", define):
        chip_family = m.group(1)
        if chip_family not in ESP32_CHIP_FAMILIES:
            raise Exception(f"Unsupported chip family: {chip_family}")

        chip_family = ESP32_CHIP_FAMILIES[chip_family]
        break

manifest = {
    "chipFamily": chip_family,
    "parts": [
        {
            "path": str(file_base / f"{name}.bin"),
            "offset": 0x00,
        }
    ],
}

print(f"Writing manifest file:")
print(json.dumps(manifest, indent=2))

with open(file_base / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

if os.environ.get("GITHUB_JOB") is not None:
    shutil.chown(file_base / "manifest.json", GH_RUNNER_USER_UID, GH_RUNNER_USER_GID)

print("::endgroup::")

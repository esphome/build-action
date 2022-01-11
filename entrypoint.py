#!/usr/bin/python3

import subprocess
import sys
import json
import shutil
from pathlib import Path
import re
import yaml

if len(sys.argv) != 2:
    print("Usage: entrypoint.py <image_file>")
    sys.exit(1)

filename = Path(sys.argv[1])

print("::group::Compile firmware")
rc = subprocess.call(["esphome", "compile", filename])
if rc != 0:
    sys.exit(rc)
print("::endgroup::")

print("::group::Get ESPHome version")
try:
    version = subprocess.check_output(["esphome", "version"])
except subprocess.CalledProcessError as e:
    sys.exit(e.returncode)
version = version.decode("utf-8").split(" ")[1]
print(f"::set-output name=esphome-version::{version}")
print("::endgroup::")

print("::group::Get config")
try:
    config = subprocess.check_output(["esphome", "config", filename])
except subprocess.CalledProcessError as e:
    sys.exit(e.returncode)

yaml.add_multi_constructor("", lambda _, t, n: t + " " + n.value)
config = yaml.load(config.decode("utf-8"), Loader=yaml.FullLoader)

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
    idedata = subprocess.check_output(["esphome", "idedata", filename])
except subprocess.CalledProcessError as e:
    sys.exit(e.returncode)

data = json.loads(idedata.decode("utf-8"))

elf = Path(data["prog_path"])
bin = elf.with_suffix(".bin")
print("::endgroup::")

print("::group::Copy firmware file(s) to folder")
file_base.mkdir(parents=True, exist_ok=True)

shutil.copyfile(bin, file_base / "firmware.bin")

extras = data["extra"]["flash_images"]

chip_family = None
esp32 = False
define: str
for define in data["defines"]:
    if define == "USE_ESP8266":
        chip_family = "ESP8266"
        break
    elif m := re.match(r"USE_ESP32_VARIANT_(\w+)", define):
        chip_family = m.group(1)
        esp32 = True
        break

firmware_offset = 0x10000 if esp32 else 0x0

manifest = {
    "chipFamily": chip_family,
    "parts": [
        {
            "path": str(file_base / "firmware.bin"),
            "offset": firmware_offset,
        }
    ],
}

for extra in extras:
    extra_bin = extra["path"]
    new_path = file_base / Path(extra_bin).name
    shutil.copyfile(extra_bin, new_path)
    print(f"Copied {new_path}")
    manifest["parts"].append(
        {
            "path": str(new_path),
            "offset": int(extra["offset"], 16),
        }
    )
print("::endgroup::")

print("::group::Write manifest.json file")
print(f"Writing manifest file:")
print(json.dumps(manifest, indent=2))

with open(file_base / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
print("::endgroup::")

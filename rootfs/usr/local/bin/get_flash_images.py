#!/usr/bin/python3
import subprocess
import sys
import json
import shutil
from pathlib import Path
import re

if len(sys.argv) != 3:
    print("Usage: flash_images.py <image_file> <output_dir>")
    sys.exit(1)

filename = Path(sys.argv[1])
output_dir = Path(sys.argv[2])

file_base = Path(filename.stem)

try:
    idedata = subprocess.check_output(["esphome", "idedata", filename])
except subprocess.CalledProcessError as e:
    sys.exit(e.returncode)

data = json.loads(idedata.decode("utf-8"))

elf = Path(data["prog_path"])
bin = elf.with_suffix(".bin")

(output_dir / file_base).mkdir(parents=True, exist_ok=True)

shutil.copyfile(bin, output_dir / file_base / "firmware.bin")

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
    shutil.copyfile(extra_bin, output_dir / new_path)
    manifest["parts"].append(
        {
            "path": str(new_path),
            "offset": int(extra["offset"], 16),
        }
    )

with open(output_dir / file_base / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

#!/usr/bin/python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


ESP32_CHIP_FAMILIES = {
    "ESP32": "ESP32",
    "ESP32S2": "ESP32-S2",
    "ESP32S3": "ESP32-S3",
    "ESP32C3": "ESP32-C3",
    "ESP32C6": "ESP32-C6",
}


def parse_args(argv):
    """Parse the arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("configuration", help="Path to the configuration file")
    parser.add_argument("--release-summary", help="Release summary", nargs="?")
    parser.add_argument("--release-url", help="Release URL", nargs="?")

    parser.add_argument("--outputs-file", help="GitHub Outputs file", nargs="?")

    return parser.parse_args(argv[1:])


def compile_firmware(filename: Path) -> int:
    """Compile the firmware."""
    print("::group::Compile firmware")
    rc = subprocess.run(
        ["esphome", "compile", filename],
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=False,
    )
    print("::endgroup::")
    return rc.returncode


def get_esphome_version(outputs_file: str | None) -> tuple[str, int]:
    """Get the ESPHome version."""
    print("::group::Get ESPHome version")
    try:
        version = subprocess.check_output(["esphome", "version"])
    except subprocess.CalledProcessError as e:
        print("::endgroup::")
        return "", e.returncode

    version = version.decode("utf-8")
    print(version)
    version = version.split(" ")[1].strip()
    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"esphome-version={version}", file=output)
    print("::endgroup::")
    return version, 0


@dataclass
class Config:
    """Configuration data."""

    name: str
    platform: str
    original_name: str

    def dest_factory_bin(self, file_base: Path) -> Path:
        """Get the destination factory binary path."""
        if self.platform == "rp2040":
            return file_base / f"{self.name}.uf2"
        return file_base / f"{self.name}.factory.bin"

    def dest_ota_bin(self, file_base: Path) -> Path:
        """Get the destination OTA binary path."""
        return file_base / f"{self.name}.ota.bin"

    def source_factory_bin(self, elf: Path) -> Path:
        """Get the source factory binary path."""
        if self.platform == "rp2040":
            return elf.with_name("firmware.uf2")
        return elf.with_name("firmware.factory.bin")

    def source_ota_bin(self, elf: Path) -> Path:
        """Get the source OTA binary path."""
        return elf.with_name("firmware.ota.bin")


def get_config(filename: Path, outputs_file: str | None) -> tuple[Config | None, int]:
    """Get the configuration."""
    print("::group::Get config")
    try:
        config = subprocess.check_output(
            ["esphome", "config", filename], stderr=sys.stderr
        )
    except subprocess.CalledProcessError as e:
        return None, e.returncode

    config = config.decode("utf-8")
    print(config)

    yaml.add_multi_constructor("", lambda _, t, n: t + " " + n.value)
    config = yaml.load(config, Loader=yaml.FullLoader)

    original_name = config["esphome"]["name"]

    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"original_name={original_name}", file=output)

    platform = ""
    if "esp32" in config:
        platform = config["esp32"]["variant"].lower()
    elif "esp8266" in config:
        platform = "esp8266"
    elif "rp2040" in config:
        platform = "rp2040"

    name = f"{original_name}-{platform}"

    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"name={name}", file=output)
    print("::endgroup::")
    return Config(name=name, platform=platform, original_name=original_name), 0


def get_idedata(filename: Path) -> tuple[dict | None, int]:
    """Get the IDEData."""
    print("::group::Get IDEData")
    try:
        idedata = subprocess.check_output(
            ["esphome", "idedata", filename], stderr=sys.stderr
        )
    except subprocess.CalledProcessError as e:
        return None, e.returncode

    data = json.loads(idedata.decode("utf-8"))
    print(json.dumps(data, indent=2))
    print("::endgroup::")
    return data, 0


def generate_manifest(
    idedata: dict,
    factory_bin: Path,
    ota_bin: Path,
    release_summary: str | None,
    release_url: str | None,
) -> tuple[dict | None, int]:
    """Generate the manifest."""
    print("::group::Generate manifest")

    chip_family = None
    define: str
    has_factory_part = False
    for define in idedata["defines"]:
        if define == "USE_ESP8266":
            chip_family = "ESP8266"
            has_factory_part = True
            break
        if define == "USE_RP2040":
            chip_family = "RP2040"
            break
        if m := re.match(r"USE_ESP32_VARIANT_(\w+)", define):
            chip_family = m.group(1)
            if chip_family not in ESP32_CHIP_FAMILIES:
                print(f"ERROR: Unsupported chip family: {chip_family}")
                return None, 1

            chip_family = ESP32_CHIP_FAMILIES[chip_family]
            has_factory_part = True
            break

    with open(ota_bin, "rb") as f:
        ota_md5 = hashlib.md5(f.read()).hexdigest()

    manifest = {
        "chipFamily": chip_family,
        "ota": {
            "path": str(ota_bin),
            "md5": ota_md5,
        },
    }

    if release_summary:
        manifest["ota"]["summary"] = release_summary
    if release_url:
        manifest["ota"]["release_url"] = release_url

    if has_factory_part:
        manifest["parts"] = [
            {
                "path": str(factory_bin),
                "offset": 0x00,
            }
        ]

    print("Writing manifest file:")
    print(json.dumps(manifest, indent=2))

    print("::endgroup::")
    return manifest, 0


def main(argv) -> int:
    """Main entrypoint."""
    args = parse_args(argv)

    filename = Path(args.configuration)

    if (rc := compile_firmware(filename)) != 0:
        return rc

    _, rc = get_esphome_version(args.outputs_file)
    if rc != 0:
        return rc

    config, rc = get_config(filename, args.outputs_file)
    if rc != 0:
        return rc

    assert config is not None

    file_base = Path(config.name)

    idedata, rc = get_idedata(filename)
    if rc != 0:
        return rc

    print("::group::Copy firmware file(s) to folder")

    elf = Path(idedata["prog_path"])

    source_factory_bin = config.source_factory_bin(elf)
    dest_factory_bin = config.dest_factory_bin(file_base)

    source_ota_bin = config.source_ota_bin(elf)
    dest_ota_bin = config.dest_ota_bin(file_base)

    file_base.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(source_factory_bin, dest_factory_bin)
    shutil.copyfile(source_ota_bin, dest_ota_bin)

    print("::endgroup::")

    manifest, rc = generate_manifest(
        idedata,
        dest_factory_bin,
        dest_ota_bin,
        args.release_summary,
        args.release_url,
    )
    if rc != 0:
        return rc

    with open(file_base / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

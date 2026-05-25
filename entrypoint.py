#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from esphome.components.esp32 import VARIANT_FRIENDLY as ESP32_CHIP_FAMILIES

try:
    from esphome.components.rp2040 import VARIANT_FRIENDLY as RP2040_CHIP_FAMILIES
except ImportError:
    # ESPHome < the rp2040 variant PR — only RP2040 exists, no friendly-name dict.
    RP2040_CHIP_FAMILIES = {"RP2040": "RP2040"}


def parse_args(argv):
    """Parse the arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("configuration", help="Path to the configuration file")
    parser.add_argument("--release-summary", help="Release summary", nargs="?")
    parser.add_argument("--release-url", help="Release URL", nargs="?")

    complete_parser = parser.add_mutually_exclusive_group()
    complete_parser.add_argument(
        "--complete-manifest",
        help="Write complete esp-web-tools manifest.json",
        action="store_true",
        dest="complete_manifest",
    )
    complete_parser.add_argument(
        "--partial-manifest",
        help="Write partial esp-web-tools manifest.json",
        action="store_false",
        dest="complete_manifest",
    )
    parser.set_defaults(complete_manifest=False)

    parser.add_argument("--outputs-file", help="GitHub Outputs file", nargs="?")

    parser.add_argument(
        "--substitution",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        dest="substitutions",
        help=(
            "Build-time substitution in KEY=VALUE format (repeatable). "
            "Values may themselves contain '=' signs."
        ),
    )

    return parser.parse_args(argv[1:])


def parse_substitutions(items: list[str]) -> tuple[list[str], int]:
    """Parse KEY=VALUE strings into flat ``-s KEY VALUE`` args for ESPHome."""
    args: list[str] = []
    for item in items:
        key, sep, value = item.partition("=")
        if not sep:
            print(f"::error::Invalid substitution {item!r}: expected KEY=VALUE")
            return [], 2
        if not key:
            print(f"::error::Invalid substitution {item!r}: key cannot be empty")
            return [], 2
        args += ["-s", key, value]
    return args, 0


def compile_firmware(filename: Path, substitution_args: list[str]) -> int:
    """Compile the firmware."""
    print("::group::Compile firmware", flush=True)
    rc = subprocess.run(
        ["esphome"] + substitution_args + ["compile", filename],
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=False,
    )
    sys.stdout.flush()
    sys.stderr.flush()
    print("::endgroup::", flush=True)
    return rc.returncode


def get_esphome_version(outputs_file: str | None) -> tuple[str, int]:
    """Get the ESPHome version."""
    print("::group::Get ESPHome version", flush=True)
    try:
        version = subprocess.check_output(["esphome", "version"])
    except subprocess.CalledProcessError as e:
        sys.stderr.flush()
        print("::endgroup::", flush=True)
        return "", e.returncode

    version = version.decode("utf-8").strip()
    print(version)
    version = version.split(" ")[1].strip()
    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"esphome-version={version}", file=output)
    sys.stderr.flush()
    print("::endgroup::", flush=True)
    return version, 0


@dataclass
class Config:
    """Configuration data."""

    name: str
    platform: str
    variant: str
    chip_family: str | None
    has_factory_part: bool
    original_name: str
    friendly_name: str | None = None

    project_name: str | None = None
    project_version: str | None = None

    raw_config: dict | None = None

    def dest_factory_bin(self, file_base: Path) -> Path:
        """Get the destination factory binary path."""
        if self.platform == "rp2040":
            return file_base / f"{self.name}.uf2"
        return file_base / f"{self.name}.factory.bin"

    def dest_ota_bin(self, file_base: Path) -> Path:
        """Get the destination OTA binary path."""
        return file_base / f"{self.name}.ota.bin"

    def dest_elf(self, file_base: Path) -> Path:
        """Get the destination ELF path."""
        return file_base / f"{self.name}.elf"

    def source_factory_bin(self, elf: Path) -> Path:
        """Get the source factory binary path."""
        if self.platform == "rp2040":
            return elf.with_name("firmware.uf2")
        return elf.with_name("firmware.factory.bin")

    def source_ota_bin(self, elf: Path) -> Path:
        """Get the source OTA binary path."""
        return elf.with_name("firmware.ota.bin")


def parse_config(config_dict: dict) -> tuple[Config | None, int]:
    """Parse a validated ESPHome config dict into a Config object."""
    original_name = config_dict["esphome"]["name"]
    friendly_name = config_dict["esphome"].get("friendly_name")

    platform = ""
    variant = ""
    chip_family: str | None = None
    has_factory_part = False
    if esp32_config := config_dict.get("esp32"):
        # esp32c3 / esp32c6 / esp32s2 / esp32s3 / esp32p4 etc
        platform = "esp32"
        variant_upper = esp32_config["variant"]
        variant = variant_upper.lower()
        if variant_upper not in ESP32_CHIP_FAMILIES:
            print(f"ERROR: Unsupported ESP32 variant: {variant_upper}")
            return None, 1
        chip_family = ESP32_CHIP_FAMILIES[variant_upper]
        has_factory_part = True
    elif "esp8266" in config_dict:
        platform = "esp8266"
        variant = "esp8266"
        chip_family = "ESP8266"
        has_factory_part = True
    elif rp2040_config := config_dict.get("rp2040"):
        # rp2040 / rp2350
        platform = "rp2040"
        variant_upper = rp2040_config.get("variant", "RP2040")
        variant = variant_upper.lower()
        if variant_upper not in RP2040_CHIP_FAMILIES:
            print(f"ERROR: Unsupported RP2040 variant: {variant_upper}")
            return None, 1
        chip_family = RP2040_CHIP_FAMILIES[variant_upper]

    name = f"{original_name}-{variant}"

    project_name: str | None = None
    project_version: str | None = None
    if project_config := config_dict["esphome"].get("project"):
        project_name = project_config["name"]
        project_version = project_config["version"]

    return Config(
        name=name,
        platform=platform,
        variant=variant,
        chip_family=chip_family,
        has_factory_part=has_factory_part,
        original_name=original_name,
        raw_config=config_dict,
        friendly_name=friendly_name,
        project_name=project_name,
        project_version=project_version,
    ), 0


def get_config(filename: Path, outputs_file: str | None, substitution_args: list[str]) -> tuple[Config | None, int]:
    """Run `esphome config` and parse the validated YAML into a Config."""
    print("::group::Get config", flush=True)
    try:
        raw = subprocess.check_output(
            ["esphome"] + substitution_args + ["config", filename],
            stderr=sys.stderr,
        )
    except subprocess.CalledProcessError as e:
        sys.stderr.flush()
        print("::endgroup::", flush=True)
        return None, e.returncode

    raw = raw.decode("utf-8")
    print(raw)

    yaml.add_multi_constructor("", lambda _, t, n: t + " " + n.value)
    config_dict = yaml.load(raw, Loader=yaml.FullLoader)

    config, rc = parse_config(config_dict)
    if rc != 0 or config is None:
        sys.stderr.flush()
        print("::endgroup::", flush=True)
        return None, rc

    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"original-name={config.original_name}", file=output)
            print(f"name={config.name}", file=output)
            if config.project_name is not None:
                print(f"project-name={config.project_name}", file=output)
                print(f"project-version={config.project_version}", file=output)

    sys.stderr.flush()
    print("::endgroup::", flush=True)
    return config, 0


def get_idedata(filename: Path, substitution_args: list[str]) -> tuple[dict | None, int]:
    """Get the IDEData."""
    print("::group::Get IDEData", flush=True)
    try:
        idedata = subprocess.check_output(
            ["esphome"] + substitution_args + ["idedata", filename],
            stderr=sys.stderr,
        )
    except subprocess.CalledProcessError as e:
        sys.stderr.flush()
        print("::endgroup::", flush=True)
        return None, e.returncode

    data = json.loads(idedata.decode("utf-8"))
    print(json.dumps(data, indent=2))
    sys.stderr.flush()
    print("::endgroup::", flush=True)
    return data, 0


def generate_manifest_part(
    config: Config,
    factory_bin: Path,
    ota_bin: Path,
    release_summary: str | None,
    release_url: str | None,
) -> tuple[dict | None, int]:
    """Generate the manifest."""

    with open(ota_bin, "rb") as f:
        ota_md5 = hashlib.md5(f.read()).hexdigest()
        f.seek(0)
        ota_sha256 = hashlib.sha256(f.read()).hexdigest()

    manifest = {
        "chipFamily": config.chip_family,
        "ota": {
            "path": ota_bin.name,
            "md5": ota_md5,
            "sha256": ota_sha256,
        },
    }

    if release_summary:
        manifest["ota"]["summary"] = release_summary
    if release_url:
        manifest["ota"]["release_url"] = release_url

    if config.has_factory_part:
        with open(factory_bin, "rb") as f:
            factory_md5 = hashlib.md5(f.read()).hexdigest()
            f.seek(0)
            factory_sha256 = hashlib.sha256(f.read()).hexdigest()
        manifest["parts"] = [
            {
                "path": str(factory_bin.name),
                "offset": 0x00,
                "md5": factory_md5,
                "sha256": factory_sha256,
            }
        ]

    return manifest, 0


def main(argv) -> int:
    """Main entrypoint."""
    args = parse_args(argv)

    filename = Path(args.configuration)

    substitution_args, rc = parse_substitutions(args.substitutions)
    if rc != 0:
        return rc

    if (rc := compile_firmware(filename, substitution_args)) != 0:
        return rc

    esphome_version, rc = get_esphome_version(args.outputs_file)
    if rc != 0:
        return rc

    config, rc = get_config(filename, args.outputs_file, substitution_args)
    if rc != 0:
        return rc

    assert config is not None

    file_base = Path(config.name)

    idedata, rc = get_idedata(filename, substitution_args)
    if rc != 0:
        return rc

    print("::group::Copy firmware file(s) to folder")

    elf = Path(idedata["prog_path"])

    source_factory_bin = config.source_factory_bin(elf)
    dest_factory_bin = config.dest_factory_bin(file_base)

    source_ota_bin = config.source_ota_bin(elf)
    dest_ota_bin = config.dest_ota_bin(file_base)

    dest_elf = config.dest_elf(file_base)

    file_base.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(source_factory_bin, dest_factory_bin)
    print("Copied factory binary to:", dest_factory_bin)
    shutil.copyfile(source_ota_bin, dest_ota_bin)
    print("Copied OTA binary to:", dest_ota_bin)
    shutil.copyfile(elf, dest_elf)
    print("Copied ELF file to:", dest_elf)

    print("::endgroup::")

    print("::group::Generate manifest")
    manifest, rc = generate_manifest_part(
        config,
        dest_factory_bin,
        dest_ota_bin,
        args.release_summary,
        args.release_url,
    )
    if rc != 0:
        return rc

    if args.complete_manifest:
        manifest = {
            "name": config.project_name or config.friendly_name or config.original_name,
            "version": config.project_version or esphome_version,
            "home_assistant_domain": "esphome",
            "new_install_prompt_erase": False,
            "builds": [
                manifest,
            ],
        }

    print("Writing manifest file:")
    print(json.dumps(manifest, indent=2))

    with open(file_base / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("::endgroup::")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

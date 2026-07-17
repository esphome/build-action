#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import yaml
from esphome.components.esp32.const import VARIANT_FRIENDLY as ESP32_CHIP_FAMILIES
from esphome.components.libretiny.const import (
    FAMILY_FRIENDLY as LIBRETINY_CHIP_FAMILIES,
)
from esphome.components.rp2.const import VARIANT_FRIENDLY as RP2_CHIP_FAMILIES

LIBRETINY_PLATFORMS: tuple[str, ...] = ("bk72xx", "ln882x", "rtl87xx")


def parse_args(argv: list[str]) -> argparse.Namespace:
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
        raw_version = subprocess.check_output(["esphome", "version"])
    except subprocess.CalledProcessError as e:
        sys.stderr.flush()
        print("::endgroup::", flush=True)
        return "", e.returncode

    version = raw_version.decode("utf-8").strip()
    print(version)
    version = version.split(" ")[1].strip()
    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"esphome-version={version}", file=output)
    sys.stderr.flush()
    print("::endgroup::", flush=True)
    return version, 0


def check_esphome_version(version: str) -> int:
    """Ensure the ESPHome version meets the action's minimum.

    The minimum comes from the MINIMUM_ESPHOME_VERSION environment
    variable, defined in action.yml (the single place it is set). The
    check is skipped when the variable is absent, e.g. when running
    outside the action.
    """
    minimum = os.environ.get("MINIMUM_ESPHOME_VERSION")
    if not minimum:
        return 0
    minimum_match = re.match(r"(\d+)\.(\d+)\.(\d+)", minimum)
    if not minimum_match:
        print(f"::warning::Unable to parse minimum ESPHome version {minimum!r}")
        return 0
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        print(f"::warning::Unable to parse ESPHome version {version!r}")
        return 0
    if tuple(int(group) for group in match.groups()) < tuple(
        int(group) for group in minimum_match.groups()
    ):
        print(
            f"::error::ESPHome {version} is not supported by this version of "
            f"the action; it requires at least ESPHome {minimum}. "
            "Pin an older release of esphome/build-action to build with "
            "older ESPHome versions."
        )
        return 1
    return 0


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

    raw_config: dict[str, Any] | None = None

    @property
    def is_libretiny(self) -> bool:
        """Is this a LibreTiny (bk72xx/ln882x/rtl87xx) platform?"""
        return self.platform in LIBRETINY_PLATFORMS

    @property
    def is_host(self) -> bool:
        """Is this the host platform (native executable)?"""
        return self.platform == "host"

    @property
    def uses_uf2(self) -> bool:
        """Is the flashable image a UF2 package rather than a .factory.bin?"""
        return self.platform in ("rp2", "nrf52") or self.is_libretiny

    @property
    def ota_is_factory(self) -> bool:
        """Is the OTA image the same file as the factory image?

        For LibreTiny the UF2 package doubles as the OTA image; for host
        the native executable itself is the OTA image.
        """
        return self.is_libretiny or self.is_host

    @property
    def artifacts_optional(self) -> bool:
        """May the factory/OTA images be absent from the build output?

        nRF52 artifacts depend on the configured bootloader and OTA setup,
        so any individual file may legitimately be missing.
        """
        return self.platform == "nrf52"

    def dest_factory_bin(self, file_base: Path) -> Path:
        """Get the destination factory binary path."""
        if self.is_host:
            # The native executable, named after the device.
            return file_base / self.name
        if self.uses_uf2:
            return file_base / f"{self.name}.uf2"
        return file_base / f"{self.name}.factory.bin"

    def dest_ota_bin(self, file_base: Path) -> Path:
        """Get the destination OTA binary path."""
        if self.ota_is_factory:
            return self.dest_factory_bin(file_base)
        return file_base / f"{self.name}.ota.bin"

    def dest_elf(self, file_base: Path) -> Path:
        """Get the destination ELF path."""
        return file_base / f"{self.name}.elf"

    def source_factory_bin(self, build_dir: Path) -> Path:
        """Get the source factory binary path."""
        if self.is_host:
            return build_dir / "program"
        if self.platform == "nrf52":
            return build_dir / "zephyr" / "zephyr.uf2"
        if self.uses_uf2:
            return build_dir / "firmware.uf2"
        return build_dir / "firmware.factory.bin"

    def source_ota_bin(self, build_dir: Path) -> Path:
        """Get the source OTA binary path."""
        if self.ota_is_factory:
            return self.source_factory_bin(build_dir)
        if self.platform == "nrf52":
            return build_dir / "zephyr" / "app_update.bin"
        return build_dir / "firmware.ota.bin"

    def extra_artifacts(self, build_dir: Path, file_base: Path) -> list[tuple[Path, Path]]:
        """Get additional (source, destination) artifacts to copy if present."""
        if self.platform == "nrf52":
            return [
                (build_dir / "firmware.zip", file_base / f"dfu-{self.name}.zip"),
                (build_dir / "zephyr" / "merged.hex", file_base / f"{self.name}.hex"),
                (build_dir / "zephyr" / "zephyr.hex", file_base / f"{self.name}.hex"),
            ]
        return []


def parse_config(config_dict: dict[str, Any]) -> tuple[Config | None, int]:
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
    elif rp2_config := config_dict.get("rp2"):
        # rp2040 / rp2350
        platform = "rp2"
        variant_upper = rp2_config["variant"]
        variant = variant_upper.lower()
        if variant_upper not in RP2_CHIP_FAMILIES:
            print(f"ERROR: Unsupported RP2 variant: {variant_upper}")
            return None, 1
        chip_family = RP2_CHIP_FAMILIES[variant_upper]
    elif libretiny_platform := next(
        (key for key in LIBRETINY_PLATFORMS if key in config_dict), None
    ):
        # bk7231n / bk7231t / ln882h / rtl8710b etc
        platform = libretiny_platform
        family = config_dict[libretiny_platform]["family"]
        variant = family.lower()
        if family not in LIBRETINY_CHIP_FAMILIES:
            print(f"ERROR: Unsupported LibreTiny family: {family}")
            return None, 1
        chip_family = LIBRETINY_CHIP_FAMILIES[family]
    elif "nrf52" in config_dict:
        platform = "nrf52"
        variant = "nrf52"
        chip_family = "NRF52"
    elif "host" in config_dict:
        # A native executable for the build machine's OS/arch.
        platform = "host"
        variant = "host"
        chip_family = "HOST"
    else:
        print("ERROR: Unable to detect the target platform from the configuration")
        return None, 1

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
        raw_config = subprocess.check_output(
            ["esphome"] + substitution_args + ["config", filename],
            stderr=sys.stderr,
        )
    except subprocess.CalledProcessError as e:
        sys.stderr.flush()
        print("::endgroup::", flush=True)
        return None, e.returncode

    raw = raw_config.decode("utf-8")
    print(raw)

    yaml.add_multi_constructor("", lambda _, t, n: t + " " + n.value)
    config_dict: dict[str, Any] = yaml.load(raw, Loader=yaml.FullLoader)

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


def get_idedata(filename: Path, substitution_args: list[str]) -> tuple[dict[str, Any] | None, int]:
    """Get the IDEData."""
    print("::group::Get IDEData", flush=True)
    try:
        output = subprocess.check_output(
            ["esphome"] + substitution_args + ["idedata", filename],
            stderr=sys.stderr,
        )
    except subprocess.CalledProcessError as e:
        sys.stderr.flush()
        print("::endgroup::", flush=True)
        return None, e.returncode

    data: dict[str, Any] = json.loads(output.decode("utf-8"))
    print(json.dumps(data, indent=2))
    sys.stderr.flush()
    print("::endgroup::", flush=True)
    return data, 0


def get_build_dir_from_storage(filename: Path) -> tuple[Path | None, int]:
    """Get the build output directory from the ESPHome storage file.

    `esphome idedata` only supports the PlatformIO and ESP-IDF toolchains,
    so for Zephyr-based platforms (nrf52) the build output directory is
    located via the storage JSON that `esphome compile` writes.
    """
    print("::group::Get build directory", flush=True)
    data_dir = Path(
        os.environ.get("ESPHOME_DATA_DIR", filename.parent / ".esphome")
    )
    storage_file = data_dir / "storage" / f"{filename.name}.json"
    try:
        with open(storage_file, encoding="utf-8") as f:
            storage: dict[str, Any] = json.load(f)
    except (OSError, ValueError) as e:
        print(f"::error::Unable to read storage file {storage_file}: {e}")
        print("::endgroup::", flush=True)
        return None, 1

    firmware_bin_path = storage.get("firmware_bin_path")
    if not firmware_bin_path:
        print(f"::error::No firmware_bin_path found in {storage_file}")
        print("::endgroup::", flush=True)
        return None, 1

    build_dir = Path(firmware_bin_path).parent
    print(f"Build directory: {build_dir}")
    print("::endgroup::", flush=True)
    return build_dir, 0


class ManifestOta(TypedDict):
    """The esp-web-tools manifest OTA section."""

    path: str
    md5: str
    sha256: str
    summary: NotRequired[str]
    release_url: NotRequired[str]


class ManifestPart(TypedDict):
    """A flashable part in the esp-web-tools manifest."""

    path: str
    offset: int
    md5: str
    sha256: str


class BuildManifest(TypedDict):
    """A single build entry in the esp-web-tools manifest."""

    chipFamily: str | None
    ota: NotRequired[ManifestOta]
    parts: NotRequired[list[ManifestPart]]


class CompleteManifest(TypedDict):
    """A complete esp-web-tools manifest."""

    name: str
    version: str
    home_assistant_domain: str
    new_install_prompt_erase: bool
    builds: list[BuildManifest]


def generate_manifest_part(
    config: Config,
    factory_bin: Path | None,
    ota_bin: Path | None,
    release_summary: str | None,
    release_url: str | None,
) -> tuple[BuildManifest, int]:
    """Generate the manifest."""

    manifest: BuildManifest = {
        "chipFamily": config.chip_family,
    }

    if ota_bin is not None:
        with open(ota_bin, "rb") as f:
            ota_md5 = hashlib.md5(f.read()).hexdigest()
            f.seek(0)
            ota_sha256 = hashlib.sha256(f.read()).hexdigest()

        manifest["ota"] = {
            "path": ota_bin.name,
            "md5": ota_md5,
            "sha256": ota_sha256,
        }

        if release_summary:
            manifest["ota"]["summary"] = release_summary
        if release_url:
            manifest["ota"]["release_url"] = release_url

    if config.has_factory_part and factory_bin is not None:
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


def main(argv: list[str]) -> int:
    """Main entrypoint."""
    args = parse_args(argv)

    filename = Path(args.configuration)

    substitution_args, rc = parse_substitutions(args.substitutions)
    if rc != 0:
        return rc

    esphome_version, rc = get_esphome_version(args.outputs_file)
    if rc != 0:
        return rc

    if (rc := check_esphome_version(esphome_version)) != 0:
        return rc

    if (rc := compile_firmware(filename, substitution_args)) != 0:
        return rc

    config, rc = get_config(filename, args.outputs_file, substitution_args)
    if rc != 0:
        return rc

    assert config is not None

    file_base = Path(config.name)

    elf: Path | None
    if config.platform == "nrf52":
        # `esphome idedata` does not support the Zephyr toolchain.
        build_dir, rc = get_build_dir_from_storage(filename)
        if rc != 0 or build_dir is None:
            return rc
        elf = next(
            (
                candidate
                for candidate in (
                    build_dir / "zephyr" / "zephyr.elf",
                    build_dir / "zephyr" / "zephyr" / "zephyr.elf",
                )
                if candidate.is_file()
            ),
            None,
        )
    else:
        idedata, rc = get_idedata(filename, substitution_args)
        if rc != 0:
            return rc
        assert idedata is not None
        elf = Path(idedata["prog_path"])
        build_dir = elf.parent

    print("::group::Copy firmware file(s) to folder")

    file_base.mkdir(parents=True, exist_ok=True)

    dest_factory_bin: Path | None = None
    source_factory_bin = config.source_factory_bin(build_dir)
    if source_factory_bin.is_file():
        dest_factory_bin = config.dest_factory_bin(file_base)
        # shutil.copy preserves the mode — the host platform's native
        # executable must keep its executable bit.
        shutil.copy(source_factory_bin, dest_factory_bin)
        print("Copied factory binary to:", dest_factory_bin)
    elif not config.artifacts_optional:
        print(f"::error::Factory binary {source_factory_bin} does not exist")
        print("::endgroup::")
        return 1

    dest_ota_bin: Path | None = None
    if config.ota_is_factory:
        dest_ota_bin = dest_factory_bin
    else:
        source_ota_bin = config.source_ota_bin(build_dir)
        if source_ota_bin.is_file():
            dest_ota_bin = config.dest_ota_bin(file_base)
            shutil.copyfile(source_ota_bin, dest_ota_bin)
            print("Copied OTA binary to:", dest_ota_bin)
        elif not config.artifacts_optional:
            print(f"::error::OTA binary {source_ota_bin} does not exist")
            print("::endgroup::")
            return 1

    extra_copied: list[Path] = []
    for source, dest in config.extra_artifacts(build_dir, file_base):
        if source.is_file() and dest not in extra_copied:
            shutil.copyfile(source, dest)
            print("Copied extra artifact to:", dest)
            extra_copied.append(dest)

    if dest_factory_bin is None and dest_ota_bin is None and not extra_copied:
        print(f"::error::No firmware artifacts found in {build_dir}")
        print("::endgroup::")
        return 1

    if elf is not None and elf.is_file() and not config.is_host:
        # For host the "ELF" is the native executable itself,
        # already copied above.
        dest_elf = config.dest_elf(file_base)
        shutil.copyfile(elf, dest_elf)
        print("Copied ELF file to:", dest_elf)

    print("::endgroup::")

    print("::group::Generate manifest")
    build_manifest, _ = generate_manifest_part(
        config,
        dest_factory_bin,
        dest_ota_bin,
        args.release_summary,
        args.release_url,
    )

    manifest: BuildManifest | CompleteManifest = build_manifest
    if args.complete_manifest:
        manifest = {
            "name": config.project_name or config.friendly_name or config.original_name,
            "version": config.project_version or esphome_version,
            "home_assistant_domain": "esphome",
            "new_install_prompt_erase": False,
            "builds": [
                build_manifest,
            ],
        }

    print("Writing manifest file:")
    print(json.dumps(manifest, indent=2))

    with open(file_base / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("::endgroup::")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))

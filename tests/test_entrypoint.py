from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import entrypoint  # noqa: E402


def _esphome_block(**extra: object) -> dict:
    block = {"name": "demo"}
    block.update(extra)
    return {"esphome": block}


class ParseConfigEsp32Tests(unittest.TestCase):
    def test_plain_esp32(self):
        config_dict = {
            **_esphome_block(),
            "esp32": {"variant": "ESP32", "board": "esp32dev"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.platform, "esp32")
        self.assertEqual(config.variant, "esp32")
        self.assertEqual(config.chip_family, "ESP32")
        self.assertTrue(config.has_factory_part)
        self.assertEqual(config.name, "demo-esp32")
        self.assertEqual(config.original_name, "demo")
        self.assertIsNone(config.friendly_name)

    def test_esp32_s3_variant(self):
        config_dict = {
            **_esphome_block(),
            "esp32": {"variant": "ESP32S3", "board": "esp32-s3-devkitc-1"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.variant, "esp32s3")
        self.assertEqual(config.chip_family, "ESP32-S3")
        self.assertEqual(config.name, "demo-esp32s3")

    def test_unsupported_esp32_variant_returns_error(self):
        config_dict = {
            **_esphome_block(),
            "esp32": {"variant": "ESP32Z99", "board": "made-up"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 1)
        self.assertIsNone(config)


class ParseConfigEsp8266Tests(unittest.TestCase):
    def test_esp8266(self):
        config_dict = {**_esphome_block(), "esp8266": {"board": "nodemcuv2"}}
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "esp8266")
        self.assertEqual(config.variant, "esp8266")
        self.assertEqual(config.chip_family, "ESP8266")
        self.assertTrue(config.has_factory_part)
        self.assertEqual(config.name, "demo-esp8266")


class ParseConfigRp2Tests(unittest.TestCase):
    def test_rp2_explicit_variant(self):
        config_dict = {
            **_esphome_block(),
            "rp2": {"variant": "RP2040", "board": "rpipico"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "rp2")
        self.assertEqual(config.variant, "rp2040")
        self.assertEqual(config.chip_family, "RP2040")
        self.assertFalse(config.has_factory_part)
        self.assertEqual(config.name, "demo-rp2040")

    def test_rp2_rp2350_variant(self):
        config_dict = {
            **_esphome_block(),
            "rp2": {"variant": "RP2350", "board": "rpipico2"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "rp2")
        self.assertEqual(config.variant, "rp2350")
        self.assertEqual(config.chip_family, "RP2350")
        self.assertFalse(config.has_factory_part)
        self.assertEqual(config.name, "demo-rp2350")

    def test_unsupported_rp2_variant_returns_error(self):
        config_dict = {
            **_esphome_block(),
            "rp2": {"variant": "RP9999", "board": "made-up"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 1)
        self.assertIsNone(config)


class ParseConfigLibreTinyTests(unittest.TestCase):
    def test_bk72xx(self):
        config_dict = {
            **_esphome_block(),
            "bk72xx": {"board": "generic-bk7231n-qfn32-tuya", "family": "BK7231N"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "bk72xx")
        self.assertEqual(config.variant, "bk7231n")
        self.assertEqual(config.chip_family, "BK7231N")
        self.assertFalse(config.has_factory_part)
        self.assertEqual(config.name, "demo-bk7231n")

    def test_rtl87xx(self):
        config_dict = {
            **_esphome_block(),
            "rtl87xx": {"board": "generic-rtl8710bn-2mb-788k", "family": "RTL8710B"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "rtl87xx")
        self.assertEqual(config.variant, "rtl8710b")
        self.assertEqual(config.chip_family, "RTL8710B")
        self.assertEqual(config.name, "demo-rtl8710b")

    def test_ln882x(self):
        config_dict = {
            **_esphome_block(),
            "ln882x": {"board": "generic-ln882hki-16mb", "family": "LN882H"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "ln882x")
        self.assertEqual(config.variant, "ln882h")
        self.assertEqual(config.chip_family, "LN882H")
        self.assertEqual(config.name, "demo-ln882h")

    def test_unsupported_family_returns_error(self):
        config_dict = {
            **_esphome_block(),
            "bk72xx": {"board": "made-up", "family": "BK9999"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 1)
        self.assertIsNone(config)


class ParseConfigNrf52Tests(unittest.TestCase):
    def test_nrf52(self):
        config_dict = {
            **_esphome_block(),
            "nrf52": {"board": "xiao_ble", "bootloader": "adafruit_nrf52_sd140_v7"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "nrf52")
        self.assertEqual(config.variant, "nrf52")
        self.assertEqual(config.chip_family, "NRF52")
        self.assertFalse(config.has_factory_part)
        self.assertEqual(config.name, "demo-nrf52")


class ParseConfigHostTests(unittest.TestCase):
    def test_host(self):
        config_dict = {
            **_esphome_block(),
            "host": {"mac_address": "98:35:69:AB:F6:79"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "host")
        self.assertEqual(config.variant, "host")
        self.assertEqual(config.chip_family, "HOST")
        self.assertFalse(config.has_factory_part)
        self.assertEqual(config.name, "demo-host")


class ParseConfigNoPlatformTests(unittest.TestCase):
    def test_config_without_platform_key_returns_error(self):
        config, rc = entrypoint.parse_config(_esphome_block())
        self.assertEqual(rc, 1)
        self.assertIsNone(config)


class ParseConfigMetadataTests(unittest.TestCase):
    def test_friendly_name(self):
        config_dict = {
            **_esphome_block(friendly_name="My Device"),
            "esp32": {"variant": "ESP32", "board": "esp32dev"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.friendly_name, "My Device")

    def test_project_metadata(self):
        config_dict = {
            **_esphome_block(project={"name": "vendor.widget", "version": "1.2.3"}),
            "esp32": {"variant": "ESP32", "board": "esp32dev"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.project_name, "vendor.widget")
        self.assertEqual(config.project_version, "1.2.3")

    def test_no_project_metadata(self):
        config_dict = {
            **_esphome_block(),
            "esp32": {"variant": "ESP32", "board": "esp32dev"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertIsNone(config.project_name)
        self.assertIsNone(config.project_version)


class ParseSubstitutionsTests(unittest.TestCase):
    def test_empty_input(self):
        args, rc = entrypoint.parse_substitutions([])
        self.assertEqual(rc, 0)
        self.assertEqual(args, [])

    def test_single_pair(self):
        args, rc = entrypoint.parse_substitutions(["name=demo"])
        self.assertEqual(rc, 0)
        self.assertEqual(args, ["-s", "name", "demo"])

    def test_multiple_pairs_preserve_order(self):
        args, rc = entrypoint.parse_substitutions(
            ["name=demo", "board=esp32dev", "pin=GPIO4"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(
            args,
            ["-s", "name", "demo", "-s", "board", "esp32dev", "-s", "pin", "GPIO4"],
        )

    def test_value_may_contain_equals(self):
        args, rc = entrypoint.parse_substitutions(["expr=a=b=c"])
        self.assertEqual(rc, 0)
        self.assertEqual(args, ["-s", "expr", "a=b=c"])

    def test_empty_value_is_allowed(self):
        args, rc = entrypoint.parse_substitutions(["flag="])
        self.assertEqual(rc, 0)
        self.assertEqual(args, ["-s", "flag", ""])

    def test_duplicate_keys_preserved(self):
        # Don't silently dedupe; let ESPHome's own precedence apply.
        args, rc = entrypoint.parse_substitutions(["name=A", "name=B"])
        self.assertEqual(rc, 0)
        self.assertEqual(args, ["-s", "name", "A", "-s", "name", "B"])

    def test_missing_equals_rejected(self):
        args, rc = entrypoint.parse_substitutions(["noequals"])
        self.assertEqual(rc, 2)
        self.assertEqual(args, [])

    def test_empty_key_rejected(self):
        args, rc = entrypoint.parse_substitutions(["=novalue"])
        self.assertEqual(rc, 2)
        self.assertEqual(args, [])

    def test_empty_string_rejected(self):
        args, rc = entrypoint.parse_substitutions([""])
        self.assertEqual(rc, 2)
        self.assertEqual(args, [])

    def test_first_invalid_stops_processing(self):
        args, rc = entrypoint.parse_substitutions(["ok=1", "bad", "also=ok"])
        self.assertEqual(rc, 2)
        self.assertEqual(args, [])


class ConfigPathTests(unittest.TestCase):
    @staticmethod
    def _make(platform: str, variant: str) -> entrypoint.Config:
        return entrypoint.Config(
            name=f"demo-{variant}",
            platform=platform,
            variant=variant,
            chip_family=None,
            has_factory_part=False,
            original_name="demo",
        )

    def test_rp2_uses_uf2(self):
        config = self._make("rp2", "rp2040")
        self.assertTrue(config.uses_uf2)
        self.assertFalse(config.is_libretiny)
        self.assertFalse(config.is_host)
        self.assertFalse(config.ota_is_factory)
        self.assertFalse(config.artifacts_optional)
        self.assertEqual(
            config.dest_factory_bin(Path("out")), Path("out/demo-rp2040.uf2")
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build")),
            Path("/build/firmware.uf2"),
        )
        self.assertEqual(
            config.source_ota_bin(Path("/build")),
            Path("/build/firmware.ota.bin"),
        )
        self.assertEqual(
            config.dest_ota_bin(Path("out")), Path("out/demo-rp2040.ota.bin")
        )
        self.assertEqual(config.extra_artifacts(Path("/build"), Path("out")), [])

    def test_rp2350_uses_uf2(self):
        config = self._make("rp2", "rp2350")
        self.assertEqual(
            config.dest_factory_bin(Path("out")), Path("out/demo-rp2350.uf2")
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build")),
            Path("/build/firmware.uf2"),
        )

    def test_esp32_uses_factory_bin(self):
        config = self._make("esp32", "esp32s3")
        self.assertFalse(config.uses_uf2)
        self.assertFalse(config.artifacts_optional)
        self.assertEqual(
            config.dest_factory_bin(Path("out")),
            Path("out/demo-esp32s3.factory.bin"),
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build")),
            Path("/build/firmware.factory.bin"),
        )
        self.assertEqual(
            config.source_ota_bin(Path("/build")),
            Path("/build/firmware.ota.bin"),
        )

    def test_esp8266_uses_factory_bin(self):
        config = self._make("esp8266", "esp8266")
        self.assertEqual(
            config.dest_factory_bin(Path("out")),
            Path("out/demo-esp8266.factory.bin"),
        )

    def test_libretiny_uf2_doubles_as_ota(self):
        for platform, variant in (
            ("bk72xx", "bk7231n"),
            ("ln882x", "ln882h"),
            ("rtl87xx", "rtl8710b"),
        ):
            with self.subTest(platform=platform):
                config = self._make(platform, variant)
                self.assertTrue(config.is_libretiny)
                self.assertTrue(config.uses_uf2)
                self.assertTrue(config.ota_is_factory)
                self.assertFalse(config.artifacts_optional)
                self.assertEqual(
                    config.dest_factory_bin(Path("out")),
                    Path(f"out/demo-{variant}.uf2"),
                )
                self.assertEqual(
                    config.dest_ota_bin(Path("out")),
                    Path(f"out/demo-{variant}.uf2"),
                )
                self.assertEqual(
                    config.source_factory_bin(Path("/build")),
                    Path("/build/firmware.uf2"),
                )
                self.assertEqual(
                    config.source_ota_bin(Path("/build")),
                    Path("/build/firmware.uf2"),
                )
                self.assertEqual(
                    config.extra_artifacts(Path("/build"), Path("out")), []
                )

    def test_host_paths(self):
        config = self._make("host", "host")
        self.assertTrue(config.is_host)
        self.assertFalse(config.uses_uf2)
        self.assertFalse(config.is_libretiny)
        self.assertTrue(config.ota_is_factory)
        self.assertFalse(config.artifacts_optional)
        self.assertEqual(
            config.dest_factory_bin(Path("out")), Path("out/demo-host")
        )
        self.assertEqual(
            config.dest_ota_bin(Path("out")), Path("out/demo-host")
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build")), Path("/build/program")
        )
        self.assertEqual(
            config.source_ota_bin(Path("/build")), Path("/build/program")
        )
        self.assertEqual(config.extra_artifacts(Path("/build"), Path("out")), [])

    def test_nrf52_paths(self):
        config = self._make("nrf52", "nrf52")
        self.assertTrue(config.uses_uf2)
        self.assertFalse(config.is_libretiny)
        self.assertFalse(config.ota_is_factory)
        self.assertTrue(config.artifacts_optional)
        self.assertEqual(
            config.dest_factory_bin(Path("out")), Path("out/demo-nrf52.uf2")
        )
        self.assertEqual(
            config.dest_ota_bin(Path("out")), Path("out/demo-nrf52.ota.bin")
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build")),
            Path("/build/zephyr/zephyr.uf2"),
        )
        self.assertEqual(
            config.source_ota_bin(Path("/build")),
            Path("/build/zephyr/app_update.bin"),
        )
        self.assertEqual(
            config.extra_artifacts(Path("/build"), Path("out")),
            [
                (Path("/build/firmware.zip"), Path("out/dfu-demo-nrf52.zip")),
                (Path("/build/zephyr/merged.hex"), Path("out/demo-nrf52.hex")),
                (Path("/build/zephyr/zephyr.hex"), Path("out/demo-nrf52.hex")),
            ],
        )


class GenerateManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)

        self.ota_bytes = b"ota-content"
        self.ota_bin = tmp / "demo.ota.bin"
        self.ota_bin.write_bytes(self.ota_bytes)

        self.factory_bytes = b"factory-content"
        self.factory_bin = tmp / "demo.factory.bin"
        self.factory_bin.write_bytes(self.factory_bytes)

    def _config(self, **overrides: object) -> entrypoint.Config:
        defaults: dict[str, object] = dict(
            name="demo-esp32",
            platform="esp32",
            variant="esp32",
            chip_family="ESP32",
            has_factory_part=True,
            original_name="demo",
        )
        defaults.update(overrides)
        return entrypoint.Config(**defaults)  # type: ignore[arg-type]

    def test_esp32_manifest_includes_factory_part(self):
        config = self._config()
        manifest, rc = entrypoint.generate_manifest_part(
            config, self.factory_bin, self.ota_bin, None, None
        )
        self.assertEqual(rc, 0)
        assert manifest is not None
        self.assertEqual(manifest["chipFamily"], "ESP32")
        self.assertEqual(manifest["ota"]["path"], "demo.ota.bin")
        self.assertEqual(
            manifest["ota"]["md5"], hashlib.md5(self.ota_bytes).hexdigest()
        )
        self.assertEqual(
            manifest["ota"]["sha256"], hashlib.sha256(self.ota_bytes).hexdigest()
        )
        self.assertNotIn("summary", manifest["ota"])
        self.assertNotIn("release_url", manifest["ota"])
        self.assertEqual(len(manifest["parts"]), 1)
        part = manifest["parts"][0]
        self.assertEqual(part["path"], "demo.factory.bin")
        self.assertEqual(part["offset"], 0)
        self.assertEqual(part["md5"], hashlib.md5(self.factory_bytes).hexdigest())
        self.assertEqual(
            part["sha256"], hashlib.sha256(self.factory_bytes).hexdigest()
        )

    def test_rp2040_manifest_omits_factory_part(self):
        config = self._config(
            name="demo-rp2040",
            platform="rp2",
            variant="rp2040",
            chip_family="RP2040",
            has_factory_part=False,
        )
        manifest, rc = entrypoint.generate_manifest_part(
            config, self.factory_bin, self.ota_bin, None, None
        )
        self.assertEqual(rc, 0)
        assert manifest is not None
        self.assertEqual(manifest["chipFamily"], "RP2040")
        self.assertNotIn("parts", manifest)

    def test_release_summary_and_url_propagated(self):
        config = self._config()
        manifest, rc = entrypoint.generate_manifest_part(
            config,
            self.factory_bin,
            self.ota_bin,
            "Test release",
            "https://example.com",
        )
        self.assertEqual(rc, 0)
        assert manifest is not None
        self.assertEqual(manifest["ota"]["summary"], "Test release")
        self.assertEqual(manifest["ota"]["release_url"], "https://example.com")

    def test_no_ota_bin_omits_ota_section(self):
        config = self._config(
            name="demo-nrf52",
            platform="nrf52",
            variant="nrf52",
            chip_family="NRF52",
            has_factory_part=False,
        )
        manifest, rc = entrypoint.generate_manifest_part(
            config, self.factory_bin, None, "summary", "https://example.com"
        )
        self.assertEqual(rc, 0)
        assert manifest is not None
        self.assertEqual(manifest, {"chipFamily": "NRF52"})

    def test_no_factory_bin_omits_parts_section(self):
        config = self._config()
        manifest, rc = entrypoint.generate_manifest_part(
            config, None, self.ota_bin, None, None
        )
        self.assertEqual(rc, 0)
        assert manifest is not None
        self.assertNotIn("parts", manifest)
        self.assertIn("ota", manifest)


class CheckEsphomeVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.dict(
            os.environ, {"MINIMUM_ESPHOME_VERSION": "2026.7.0"}
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_minimum_version_accepted(self):
        self.assertEqual(entrypoint.check_esphome_version("2026.7.0"), 0)

    def test_newer_version_accepted(self):
        self.assertEqual(entrypoint.check_esphome_version("2027.1.2"), 0)

    def test_dev_suffix_accepted(self):
        self.assertEqual(entrypoint.check_esphome_version("2026.8.0-dev"), 0)

    def test_beta_suffix_accepted(self):
        self.assertEqual(entrypoint.check_esphome_version("2026.7.0b2"), 0)

    def test_older_version_rejected(self):
        self.assertEqual(entrypoint.check_esphome_version("2026.6.3"), 1)
        self.assertEqual(entrypoint.check_esphome_version("2023.12.9"), 1)

    def test_unparseable_version_warns_but_passes(self):
        self.assertEqual(entrypoint.check_esphome_version("garbage"), 0)

    def test_no_minimum_env_skips_check(self):
        os.environ.pop("MINIMUM_ESPHOME_VERSION", None)
        self.assertEqual(entrypoint.check_esphome_version("2023.12.9"), 0)

    def test_unparseable_minimum_warns_but_passes(self):
        os.environ["MINIMUM_ESPHOME_VERSION"] = "garbage"
        self.assertEqual(entrypoint.check_esphome_version("2023.12.9"), 0)


class GetBuildDirFromStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.filename = self.tmp / "demo.yaml"
        self.storage_file = self.tmp / ".esphome" / "storage" / "demo.yaml.json"
        self.storage_file.parent.mkdir(parents=True)

        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("ESPHOME_DATA_DIR", None)

    def _write_storage(self, data: dict) -> None:
        self.storage_file.write_text(json.dumps(data), encoding="utf-8")

    def test_valid_storage(self):
        self._write_storage(
            {"firmware_bin_path": str(self.tmp / "build" / "firmware.bin")}
        )
        build_dir, rc = entrypoint.get_build_dir_from_storage(self.filename)
        self.assertEqual(rc, 0)
        self.assertEqual(build_dir, self.tmp / "build")

    def test_data_dir_env_override(self):
        other_data_dir = self.tmp / "other-data"
        storage_file = other_data_dir / "storage" / "demo.yaml.json"
        storage_file.parent.mkdir(parents=True)
        storage_file.write_text(
            json.dumps({"firmware_bin_path": str(self.tmp / "out" / "firmware.bin")}),
            encoding="utf-8",
        )
        os.environ["ESPHOME_DATA_DIR"] = str(other_data_dir)
        build_dir, rc = entrypoint.get_build_dir_from_storage(self.filename)
        self.assertEqual(rc, 0)
        self.assertEqual(build_dir, self.tmp / "out")

    def test_missing_storage_file(self):
        build_dir, rc = entrypoint.get_build_dir_from_storage(self.filename)
        self.assertEqual(rc, 1)
        self.assertIsNone(build_dir)

    def test_invalid_json(self):
        self.storage_file.write_text("{not json", encoding="utf-8")
        build_dir, rc = entrypoint.get_build_dir_from_storage(self.filename)
        self.assertEqual(rc, 1)
        self.assertIsNone(build_dir)

    def test_missing_firmware_bin_path(self):
        self._write_storage({"name": "demo"})
        build_dir, rc = entrypoint.get_build_dir_from_storage(self.filename)
        self.assertEqual(rc, 1)
        self.assertIsNone(build_dir)


class MainFlowTests(unittest.TestCase):
    """Exercise main()'s artifact copy and manifest flow with the
    esphome subprocess helpers stubbed out."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self._old_cwd = Path.cwd()
        os.chdir(self.tmp)
        self.addCleanup(os.chdir, self._old_cwd)
        self.build_dir = self.tmp / "build"

        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("ESPHOME_DATA_DIR", None)
        os.environ["MINIMUM_ESPHOME_VERSION"] = "2026.7.0"

    @staticmethod
    def _config(**overrides: object) -> entrypoint.Config:
        defaults: dict[str, object] = dict(
            name="demo-esp32",
            platform="esp32",
            variant="esp32",
            chip_family="ESP32",
            has_factory_part=True,
            original_name="demo",
        )
        defaults.update(overrides)
        return entrypoint.Config(**defaults)  # type: ignore[arg-type]

    def _write_build_files(self, build_files: dict[str, bytes]) -> None:
        for rel, content in build_files.items():
            path = self.build_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def _write_storage(self) -> None:
        storage_file = self.tmp / ".esphome" / "storage" / "demo.yaml.json"
        storage_file.parent.mkdir(parents=True, exist_ok=True)
        storage_file.write_text(
            json.dumps({"firmware_bin_path": str(self.build_dir / "firmware.bin")}),
            encoding="utf-8",
        )

    def _run_main(
        self,
        config: entrypoint.Config,
        build_files: dict[str, bytes],
        extra_argv: list[str] | None = None,
    ) -> tuple[int, mock.MagicMock]:
        self._write_build_files(build_files)
        elf = self.build_dir / "firmware.elf"
        idedata_mock = mock.MagicMock(
            return_value=({"prog_path": str(elf)}, 0)
        )
        with (
            mock.patch.object(entrypoint, "compile_firmware", return_value=0),
            mock.patch.object(
                entrypoint, "get_esphome_version", return_value=("2026.7.0", 0)
            ),
            mock.patch.object(entrypoint, "get_config", return_value=(config, 0)),
            mock.patch.object(entrypoint, "get_idedata", idedata_mock),
        ):
            rc = entrypoint.main(
                ["entrypoint.py", "demo.yaml"] + (extra_argv or [])
            )
        return rc, idedata_mock

    def _manifest(self, name: str) -> dict:
        with open(self.tmp / name / "manifest.json", encoding="utf-8") as f:
            return json.load(f)

    def test_esp32_full_flow_complete_manifest(self):
        rc, _ = self._run_main(
            self._config(project_name="vendor.widget", project_version="1.2.3"),
            {
                "firmware.factory.bin": b"factory",
                "firmware.ota.bin": b"ota",
                "firmware.elf": b"elf",
            },
            [
                "--complete-manifest",
                "--release-summary",
                "Test release",
                "--release-url",
                "https://example.com",
            ],
        )
        self.assertEqual(rc, 0)
        out = self.tmp / "demo-esp32"
        self.assertEqual(
            (out / "demo-esp32.factory.bin").read_bytes(), b"factory"
        )
        self.assertEqual((out / "demo-esp32.ota.bin").read_bytes(), b"ota")
        self.assertEqual((out / "demo-esp32.elf").read_bytes(), b"elf")
        manifest = self._manifest("demo-esp32")
        self.assertEqual(manifest["name"], "vendor.widget")
        self.assertEqual(manifest["version"], "1.2.3")
        build = manifest["builds"][0]
        self.assertEqual(build["chipFamily"], "ESP32")
        self.assertEqual(build["ota"]["path"], "demo-esp32.ota.bin")
        self.assertEqual(build["ota"]["summary"], "Test release")
        self.assertEqual(build["ota"]["release_url"], "https://example.com")
        self.assertEqual(build["parts"][0]["path"], "demo-esp32.factory.bin")

    def test_esp32_missing_factory_bin_fails(self):
        rc, _ = self._run_main(
            self._config(),
            {"firmware.ota.bin": b"ota", "firmware.elf": b"elf"},
        )
        self.assertEqual(rc, 1)

    def test_esp32_missing_ota_bin_fails(self):
        rc, _ = self._run_main(
            self._config(),
            {"firmware.factory.bin": b"factory", "firmware.elf": b"elf"},
        )
        self.assertEqual(rc, 1)

    def test_libretiny_uf2_flow(self):
        rc, _ = self._run_main(
            self._config(
                name="demo-bk7231n",
                platform="bk72xx",
                variant="bk7231n",
                chip_family="BK7231N",
                has_factory_part=False,
            ),
            {"firmware.uf2": b"uf2", "firmware.elf": b"elf"},
        )
        self.assertEqual(rc, 0)
        out = self.tmp / "demo-bk7231n"
        self.assertEqual((out / "demo-bk7231n.uf2").read_bytes(), b"uf2")
        self.assertEqual((out / "demo-bk7231n.elf").read_bytes(), b"elf")
        self.assertFalse((out / "demo-bk7231n.ota.bin").exists())
        manifest = self._manifest("demo-bk7231n")
        self.assertEqual(manifest["chipFamily"], "BK7231N")
        self.assertEqual(manifest["ota"]["path"], "demo-bk7231n.uf2")
        self.assertNotIn("parts", manifest)

    def _nrf52_config(self) -> entrypoint.Config:
        return self._config(
            name="demo-nrf52",
            platform="nrf52",
            variant="nrf52",
            chip_family="NRF52",
            has_factory_part=False,
        )

    def test_nrf52_full_flow(self):
        self._write_storage()
        rc, idedata_mock = self._run_main(
            self._nrf52_config(),
            {
                "zephyr/zephyr.uf2": b"uf2",
                "zephyr/app_update.bin": b"app-update",
                "firmware.zip": b"dfu",
                "zephyr/merged.hex": b"merged",
                "zephyr/zephyr.hex": b"plain",
                "zephyr/zephyr.elf": b"elf",
            },
        )
        self.assertEqual(rc, 0)
        idedata_mock.assert_not_called()
        out = self.tmp / "demo-nrf52"
        self.assertEqual((out / "demo-nrf52.uf2").read_bytes(), b"uf2")
        self.assertEqual((out / "demo-nrf52.ota.bin").read_bytes(), b"app-update")
        self.assertEqual((out / "dfu-demo-nrf52.zip").read_bytes(), b"dfu")
        # merged.hex takes precedence over zephyr.hex for the same destination
        self.assertEqual((out / "demo-nrf52.hex").read_bytes(), b"merged")
        self.assertEqual((out / "demo-nrf52.elf").read_bytes(), b"elf")
        manifest = self._manifest("demo-nrf52")
        self.assertEqual(manifest["chipFamily"], "NRF52")
        self.assertEqual(manifest["ota"]["path"], "demo-nrf52.ota.bin")
        self.assertNotIn("parts", manifest)

    def test_nrf52_uf2_only_omits_ota(self):
        self._write_storage()
        rc, _ = self._run_main(
            self._nrf52_config(), {"zephyr/zephyr.uf2": b"uf2"}
        )
        self.assertEqual(rc, 0)
        out = self.tmp / "demo-nrf52"
        self.assertTrue((out / "demo-nrf52.uf2").exists())
        self.assertFalse((out / "demo-nrf52.ota.bin").exists())
        self.assertFalse((out / "demo-nrf52.elf").exists())
        manifest = self._manifest("demo-nrf52")
        self.assertEqual(manifest, {"chipFamily": "NRF52"})

    def test_nrf52_nested_elf_is_found(self):
        self._write_storage()
        rc, _ = self._run_main(
            self._nrf52_config(),
            {
                "zephyr/zephyr.uf2": b"uf2",
                "zephyr/zephyr/zephyr.elf": b"nested-elf",
            },
        )
        self.assertEqual(rc, 0)
        out = self.tmp / "demo-nrf52"
        self.assertEqual((out / "demo-nrf52.elf").read_bytes(), b"nested-elf")

    def test_nrf52_no_artifacts_fails(self):
        self._write_storage()
        self.build_dir.mkdir(parents=True, exist_ok=True)
        rc, _ = self._run_main(self._nrf52_config(), {})
        self.assertEqual(rc, 1)

    def test_nrf52_missing_storage_fails(self):
        rc, _ = self._run_main(
            self._nrf52_config(), {"zephyr/zephyr.uf2": b"uf2"}
        )
        self.assertEqual(rc, 1)

    def test_host_flow(self):
        self.build_dir.mkdir(parents=True, exist_ok=True)
        program = self.build_dir / "program"
        program.write_bytes(b"native-binary")
        program.chmod(0o755)
        # For host the idedata prog_path is the program binary itself.
        with (
            mock.patch.object(entrypoint, "compile_firmware", return_value=0),
            mock.patch.object(
                entrypoint, "get_esphome_version", return_value=("2026.7.0", 0)
            ),
            mock.patch.object(
                entrypoint,
                "get_config",
                return_value=(
                    self._config(
                        name="demo-host",
                        platform="host",
                        variant="host",
                        chip_family="HOST",
                        has_factory_part=False,
                    ),
                    0,
                ),
            ),
            mock.patch.object(
                entrypoint,
                "get_idedata",
                return_value=({"prog_path": str(program)}, 0),
            ),
        ):
            rc = entrypoint.main(["entrypoint.py", "demo.yaml"])
        self.assertEqual(rc, 0)
        out = self.tmp / "demo-host"
        binary = out / "demo-host"
        self.assertEqual(binary.read_bytes(), b"native-binary")
        self.assertTrue(os.access(binary, os.X_OK))
        self.assertFalse((out / "demo-host.ota.bin").exists())
        self.assertFalse((out / "demo-host.elf").exists())
        manifest = self._manifest("demo-host")
        self.assertEqual(manifest["chipFamily"], "HOST")
        self.assertEqual(manifest["ota"]["path"], "demo-host")
        self.assertEqual(
            manifest["ota"]["md5"], hashlib.md5(b"native-binary").hexdigest()
        )
        self.assertNotIn("parts", manifest)

    def test_old_esphome_version_fails_before_compile(self):
        compile_mock = mock.MagicMock(return_value=0)
        with (
            mock.patch.object(entrypoint, "compile_firmware", compile_mock),
            mock.patch.object(
                entrypoint, "get_esphome_version", return_value=("2026.6.3", 0)
            ),
        ):
            rc = entrypoint.main(["entrypoint.py", "demo.yaml"])
        self.assertEqual(rc, 1)
        compile_mock.assert_not_called()

    def test_idedata_failure_propagates(self):
        with (
            mock.patch.object(entrypoint, "compile_firmware", return_value=0),
            mock.patch.object(
                entrypoint, "get_esphome_version", return_value=("2026.7.0", 0)
            ),
            mock.patch.object(
                entrypoint, "get_config", return_value=(self._config(), 0)
            ),
            mock.patch.object(entrypoint, "get_idedata", return_value=(None, 3)),
        ):
            rc = entrypoint.main(["entrypoint.py", "demo.yaml"])
        self.assertEqual(rc, 3)


if __name__ == "__main__":
    unittest.main()

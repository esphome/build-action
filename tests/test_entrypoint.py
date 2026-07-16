from __future__ import annotations

import hashlib
import sys
import tempfile
import types
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

    @mock.patch.dict(entrypoint.RP2_CHIP_FAMILIES, {"RP2350": "RP2350"}, clear=False)
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


class ParseConfigRp2040Tests(unittest.TestCase):
    # `rp2040` is the deprecated alias of the `rp2` platform key, and the
    # only key older ESPHome releases emit — it must keep working.
    def test_rp2040_explicit_variant(self):
        config_dict = {
            **_esphome_block(),
            "rp2040": {"variant": "RP2040", "board": "rpipico"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "rp2040")
        self.assertEqual(config.variant, "rp2040")
        self.assertEqual(config.chip_family, "RP2040")
        self.assertFalse(config.has_factory_part)
        self.assertEqual(config.name, "demo-rp2040")

    def test_rp2040_without_variant_key_defaults_to_rp2040(self):
        # Older ESPHome (pre variant PR) emits no `variant` key in the
        # rp2040 block — we must default to RP2040 so the action still
        # works against historical releases.
        config_dict = {**_esphome_block(), "rp2040": {"board": "rpipico"}}
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.variant, "rp2040")
        self.assertEqual(config.chip_family, "RP2040")

    @mock.patch.dict(entrypoint.RP2_CHIP_FAMILIES, {"RP2350": "RP2350"}, clear=False)
    def test_rp2350_variant(self):
        config_dict = {
            **_esphome_block(),
            "rp2040": {"variant": "RP2350", "board": "rpipico2"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "rp2040")
        self.assertEqual(config.variant, "rp2350")
        self.assertEqual(config.chip_family, "RP2350")
        self.assertFalse(config.has_factory_part)
        self.assertEqual(config.name, "demo-rp2350")

    def test_unsupported_rp2040_variant_returns_error(self):
        config_dict = {
            **_esphome_block(),
            "rp2040": {"variant": "RP9999", "board": "made-up"},
        }
        config, rc = entrypoint.parse_config(config_dict)
        self.assertEqual(rc, 1)
        self.assertIsNone(config)


class ParseConfigNoPlatformTests(unittest.TestCase):
    def test_config_without_platform_key(self):
        config, rc = entrypoint.parse_config(_esphome_block())
        self.assertEqual(rc, 0)
        assert config is not None
        self.assertEqual(config.platform, "")
        self.assertEqual(config.variant, "")
        self.assertIsNone(config.chip_family)
        self.assertFalse(config.has_factory_part)
        self.assertEqual(config.name, "demo-")


class LoadRp2ChipFamiliesTests(unittest.TestCase):
    # A `None` entry in sys.modules makes `import` raise ImportError for
    # that module, which is how the missing-component cases are simulated.
    @staticmethod
    def _fake_component(variants: dict[str, str]) -> types.ModuleType:
        module = types.ModuleType("fake_component")
        module.VARIANT_FRIENDLY = variants
        return module

    def test_rp2_component_preferred(self):
        variants = {"RP2040": "RP2040", "RP2350": "RP2350"}
        with mock.patch.dict(
            sys.modules, {"esphome.components.rp2": self._fake_component(variants)}
        ):
            self.assertEqual(entrypoint._load_rp2_chip_families(), variants)

    def test_falls_back_to_rp2040_component(self):
        variants = {"RP2040": "RP2040"}
        with mock.patch.dict(
            sys.modules,
            {
                "esphome.components.rp2": None,
                "esphome.components.rp2040": self._fake_component(variants),
            },
        ):
            self.assertEqual(entrypoint._load_rp2_chip_families(), variants)

    def test_falls_back_to_static_dict_when_both_missing(self):
        with mock.patch.dict(
            sys.modules,
            {
                "esphome.components.rp2": None,
                "esphome.components.rp2040": None,
            },
        ):
            self.assertEqual(
                entrypoint._load_rp2_chip_families(), {"RP2040": "RP2040"}
            )


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
        self.assertEqual(
            config.dest_factory_bin(Path("out")), Path("out/demo-rp2040.uf2")
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build/firmware.elf")),
            Path("/build/firmware.uf2"),
        )

    def test_rp2040_uses_uf2(self):
        config = self._make("rp2040", "rp2040")
        self.assertEqual(
            config.dest_factory_bin(Path("out")), Path("out/demo-rp2040.uf2")
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build/firmware.elf")),
            Path("/build/firmware.uf2"),
        )

    def test_rp2350_uses_uf2(self):
        config = self._make("rp2040", "rp2350")
        self.assertEqual(
            config.dest_factory_bin(Path("out")), Path("out/demo-rp2350.uf2")
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build/firmware.elf")),
            Path("/build/firmware.uf2"),
        )

    def test_esp32_uses_factory_bin(self):
        config = self._make("esp32", "esp32s3")
        self.assertEqual(
            config.dest_factory_bin(Path("out")),
            Path("out/demo-esp32s3.factory.bin"),
        )
        self.assertEqual(
            config.source_factory_bin(Path("/build/firmware.elf")),
            Path("/build/firmware.factory.bin"),
        )

    def test_esp8266_uses_factory_bin(self):
        config = self._make("esp8266", "esp8266")
        self.assertEqual(
            config.dest_factory_bin(Path("out")),
            Path("out/demo-esp8266.factory.bin"),
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
            platform="rp2040",
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


if __name__ == "__main__":
    unittest.main()

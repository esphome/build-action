# ESPHome Build action

![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/esphome/build-action)

This action takes a yaml file for an ESPHome device and will compile and output
the build firmware file and a partial `manifest.json` file that can be used to flash
a device via [ESP Web Tools](https://esphome.github.io/esp-web-tools).

Supported platforms:

- ESP32 (all variants)
- ESP8266
- RP2040 / RP2350
- LibreTiny (BK72xx, RTL87xx, LN882x)
- nRF52
- Host (a native executable for the build machine's OS/architecture)

This action requires ESPHome 2026.7.0 or newer (the `version` input must not
resolve to anything older). Pin an older release of this action to build with
older ESPHome versions.

Releases of this action are immutable and no floating major tags (eg. `v7`)
are published — pin a full release tag or, preferably, the commit SHA of a
release.

## Example usage

```yaml
uses: esphome/build-action@v7.0.0
with:
  yaml-file: my_configuration.yaml
```

To pass build-time substitutions:

```yaml
uses: esphome/build-action@v7.0.0
with:
  yaml-file: my_configuration.yaml
  substitutions: |
    name=my-device
    board_pin=GPIO4
```

This action is used by the [ESPHome publish workflow](https://github.com/esphome/workflows/blob/main/.github/workflows/publish.yml) that is used to compile firmware and publish simple GitHub pages sites for projects.

## Inputs

| Name                | Default  | Description                                                                             |
| ------------------- | -------- | --------------------------------------------------------------------------------------- |
| `yaml-file`         | _None_   | The YAML file to be compiled.                                                           |
| `version`           | `latest` | The ESPHome version to build using.                                                     |
| `release-summary`   | _None_   | A small summary of the release that will be added to the manifest file.                 |
| `release-url`       | _None_   | A URL to the release page that will be added to the manifest file.                      |
| `complete-manifest` | `false`  | Whether to output a complete manifest file. Defaults to output a partial manifest only. |
| `substitutions`     | _None_   | Build-time substitutions passed to ESPHome via the `-s` flag. One `key=value` pair per line. |

## Outputs

| Name              | Description                                                                                              |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| `name`            | The name of the device in yaml with the platform variant appended (eg. `-esp32`, `-rp2040`, `-bk7231n`). |
| `version`         | The ESPHome version used during build.                                                                   |
| `original-name`   | The original name of the device in yaml.                                                                 |
| `project-name`    | The name of the project in yaml. `esphome.project.name`                                                  |
| `project-version` | The version of the project in yaml. `esphome.project.version`                                            |

## Output files

This action will output a folder named with the output `name` containing the firmware
files for the platform along with:

- `manifest.json`
  - If `complete-manifest` is set to `true` then this file is directly usable by esp-web-tools.
  - Otherwise, this goes into the `builds` section of an esp-web-tools manifest.json.
- `{name}.elf` - The ELF file with debug symbols for the built firmware.

The firmware files depend on the platform:

- ESP32 / ESP8266
  - `{name}.factory.bin` - The firmware to be flashed with esp-web-tools.
  - `{name}.ota.bin` - The firmware that can be flashed over-the-air to the device using the [Managed Updates via HTTP Request](https://esphome.io/components/update/http_request).
- RP2040 / RP2350
  - `{name}.uf2` - The firmware to be flashed via the UF2 bootloader (USB mass storage).
  - `{name}.ota.bin` - The firmware that can be flashed over-the-air to the device.
- LibreTiny (BK72xx / RTL87xx / LN882x)
  - `{name}.uf2` - The UF2 firmware package, used both for initial flashing (e.g. with ltchiptool) and for over-the-air updates; the manifest `ota` section points at this file.
- nRF52
  - `{name}.uf2` - The firmware to be flashed via the Adafruit nRF52 bootloader (USB mass storage), when built for that bootloader.
  - `dfu-{name}.zip` - The DFU package for flashing with adafruit-nrfutil, when available.
  - `{name}.ota.bin` - The application update image, when available.
  - `{name}.hex` - The merged HEX image for flashing via SWD, when available.
- Host
  - `{name}` - A native executable that can be run directly on a machine matching the build OS/architecture (choose the runner OS/arch in your workflow to match the target). No `manifest.json` or `{name}.elf` is produced.

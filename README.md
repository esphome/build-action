# ESPHome Build action

![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/esphome/build-action)

This action takes a yaml file for an ESPHome device and will compile and output
the build firmware file and a partial `manifest.json` file that can be used to flash
a device via [ESP Web Tools](https://esphome.github.io/esp-web-tools).

## Example usage

```yaml
uses: esphome/build-action@v1
with:
  yaml_file: my_configuration.yaml
```

This action is used by the [ESPHome publish workflow](https://github.com/esphome/workflows/blob/main/.github/workflows/publish.yml) that is used to compile firmware and publish simple GitHub pages sites for projects.

## Inputs

| Name                | Default       | Description                                                                             |
| ------------------- | ------------- | --------------------------------------------------------------------------------------- |
| `yaml_file`         | _None_        | The YAML file to be compiled.                                                           |
| `version`           | `latest`      | The ESPHome version to build using.                                                     |
| `platform`          | `linux/amd64` | The docker platform to use during build. (linux/amd64, linux/arm64, linux/arm/v7)       |
| `cache`             | `false`       | Whether to cache the build folder.                                                      |
| `release_summary`   | _None_        | A small summary of the release that will be added to the manifest file.                 |
| `release_url`       | _None_        | A URL to the release page that will be added to the manifest file.                      |
| `complete-manifest` | `false`       | Whether to output a complete manifest file. Defaults to output a partial manifest only. |

## Outputs

| Name              | Description                                                                       |
| ----------------- | --------------------------------------------------------------------------------- |
| `name`            | The name of the device in yaml with the platform (eg. ESP32 or ESP8266) appended. |
| `version`         | The ESPHome version used during build.                                            |
| `original-name`   | The original name of the device in yaml.                                          |
| `project-name`    | The name of the project in yaml. `esphome.project.name`                           |
| `project-version` | The version of the project in yaml. `esphome.project.version`                     |

## Output files

This action will output a folder named with the output `name` and will contain three files:

- `manifest.json` 
  - If `complete-manifest` is set to `true` then this file is directly usable by esp-web-tools.
  - Otherwise, this goes into the `builds` section of an esp-web-tools manifest.json.
- `{name}.factory.bin` - The firmware to be flashed with esp-web-tools.
- `{name}.ota.bin` - The firmware that can be flashed over-the-air to the device using the [Managed Updated via HTTP Request](https://esphome.io/components/update/http_request).

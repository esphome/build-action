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

Name        | Default       | Description  
------------|---------------|------------
`yaml_file` | _None_        | The YAML file to be compiled.
`version`   | `latest`      | The ESPHome version to build using.
`platform`  | `linux/amd64` | The docker platform to use during build. (linux/amd64, linux/arm64, linux/arm/v7)
`cache`     | `false`       | Whether to cache the build folder.

## Outputs

Name      | Description  
----------|------------
`name`    | The name of the device in yaml with the platform (eg. ESP32 or ESP8266) appended.
`version` | The ESPHome version used during build.

## Output files

This action will output a folder named with the output `name` and will contain two files, `{name}.bin` and `manifest.json`.

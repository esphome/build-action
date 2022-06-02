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

## Inputs

Name | Default | Description  
-----|---------|------------
`yaml_file` | _None_   | The YAML file to be compiled.
`version`   | `latest` | The ESPHome version to build using.

## Outputs

Name   | Description  
-------|------------
`name` | The name of the device in yaml with the platform (eg. ESP32 or ESP8266) appended.

## Output files

This action will output a folder named with the output `name` and will contain two files, `{name}.bin` and `manifest.json`.

# ESPHome Build action

## inputs

### `yaml_file`

**Required**. The YAML filename to be compiled.

### `esphome_version`

**Optional**. The version of ESPHome to use. Defaults to the latest stable version.

## Example usage

```yaml

uses: esphome/build
with:
  yaml_file: my_configuration.yaml
  esphome_version: "2021.10.3"

```

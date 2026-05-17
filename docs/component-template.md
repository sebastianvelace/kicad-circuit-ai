# Component YAML Template

Use this as a starting point when adding a new component.

```yaml
# components/COMPONENT_NAME.yaml
# Brief description of the component

component:
  name: COMPONENT_NAME       # Primary name (ALL CAPS recommended)
  aliases: []                # Common variants, part suffixes, manufacturer equivalents
  package: DIP-8             # Most common package
  category: timer            # See categories below
  datasheet: https://...     # Official datasheet URL

pins:
  1:
    name: GND                # Pin name from datasheet
    function: ground         # Semantic function (see list below)
    type: power_input        # KiCad pin type
    must_connect_to: GND     # Required net (omit if any net is OK)
    must_not_be: []          # Forbidden nets (e.g., [GND] for a VCC pin)
    warn_if_floating: false  # true if leaving unconnected is dangerous
    optional: false          # true if this pin can be left unconnected
    critical: false          # true to elevate errors to CRITICAL severity
    recommended: ""          # Recommended external connection (shown as tip)
    notes: ""                # Educational explanation — write for students!

  2:
    name: IN
    function: input
    type: input
    must_not_be: [GND, VCC]
    warn_if_floating: true
    notes: >
      Multi-line notes use YAML block scalar.
      Write as if explaining to a student seeing this component for the first time.
      What happens if they wire it wrong? What's the correct connection?

# Optional: common circuit topologies
common_configurations:
  basic:
    description: "Typical usage description"
    required_connections:
      - "Short description of each required connection"
```

## Categories

`timer`, `op_amp`, `comparator`, `voltage_regulator`, `ldo_regulator`,
`microcontroller`, `motor_driver`, `gate_driver`, `level_shifter`,
`adc`, `dac`, `sensor`, `rf_module`, `display_driver`, `io_expander`,
`memory`, `logic`, `power_switch`, `mosfet_driver`, `oscillator`

## Semantic functions

`ground`, `positive_supply`, `negative_supply`, `output`, `input`,
`clock`, `reset`, `enable`, `chip_select`, `spi_mosi`, `spi_miso`,
`spi_sck`, `i2c_sda`, `i2c_scl`, `uart_tx`, `uart_rx`,
`analog_input`, `analog_output`, `pwm_output`, `trigger_input`,
`threshold`, `discharge`, `control_voltage`, `offset_null`, `no_connect`,
`motor_supply`, `logic_supply`, `analog_supply`, `analog_reference`

## KiCad pin types

`power_input`, `power_output`, `input`, `output`, `bidirectional`,
`tri_state`, `passive`, `open_collector`, `open_emitter`, `no_connect`

## Net keywords (normalized automatically)

These net names are treated as equivalent groups:
- **GND group**: `GND`, `GND0`, `GNDA`, `AGND`, `DGND`, `VSS`, `0V`, `EARTH`
- **VCC group**: `VCC`, `VDD`, `+5V`, `+3V3`, `+3.3V`, `AVCC`, `VBUS`
- **V_MINUS group**: `V-`, `VEE`, `-5V`, `-12V`, `-15V`

Use these in `must_connect_to` and `must_not_be` — they'll match any equivalent net name.

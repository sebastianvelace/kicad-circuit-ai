# Contributing to kicad-circuit-ai

## The fastest way to contribute: add a component

Every IC in `components/` was contributed by someone who used that component in a course or project. Adding a new one takes about 10 minutes.

### Step 1: Copy the template

```bash
cp components/NE555.yaml components/YOUR_COMPONENT.yaml
```

### Step 2: Fill in the pins

Open the datasheet and fill in each pin:

```yaml
# components/LM741.yaml
component:
  name: LM741
  aliases: [uA741, MC1741, LM741CN]
  package: DIP-8
  category: op_amp
  datasheet: https://www.ti.com/lit/ds/symlink/lm741.pdf

pins:
  1:
    name: OFFSET_NULL_A
    function: offset_null
    type: input
    optional: true
    notes: "Connect 10kΩ pot between pins 1 and 5 for offset nulling. Leave floating if not needed."
  2:
    name: IN_MINUS
    function: inverting_input
    type: input
    must_not_be: [VCC, GND]
    notes: "Inverting input. Connecting directly to power rails will saturate the output."
  3:
    name: IN_PLUS
    function: non_inverting_input
    type: input
    must_not_be: [VCC, GND]
    notes: "Non-inverting input."
  4:
    name: V_MINUS
    function: negative_supply
    type: power_input
    must_connect_to: V_MINUS
    must_not_be: [VCC, GND]
    critical: true
    notes: "Negative supply rail. Typically -5V to -15V. Do NOT connect to GND in split-supply designs."
  5:
    name: OFFSET_NULL_B
    function: offset_null
    type: input
    optional: true
  6:
    name: OUT
    function: output
    type: output
    notes: "Output. Do not connect directly to power rails."
  7:
    name: V_PLUS
    function: positive_supply
    type: power_input
    must_connect_to: VCC
    must_not_be: [GND]
    critical: true
    notes: "Positive supply rail. Typically +5V to +15V."
  8:
    name: NC
    function: no_connect
    type: no_connect
    notes: "No internal connection."
```

### Step 3: Add a test fixture

Create a minimal netlist XML in `tests/fixtures/` showing a common mistake for this component:

```xml
<?xml version="1.0" encoding="utf-8"?>
<export version="D">
  <components>
    <comp ref="U1">
      <value>LM741</value>
      <libsource lib="Amplifier_Operational" part="LM741" description="Op-Amp"/>
    </comp>
  </components>
  <nets>
    <net code="1" name="GND">
      <node ref="U1" pin="4" pinfunction="V_MINUS"/>
    </net>
    <net code="2" name="+15V">
      <node ref="U1" pin="7" pinfunction="V_PLUS"/>
    </net>
    <net code="3" name="Net-IN_PLUS">
      <node ref="U1" pin="3" pinfunction="IN_PLUS"/>
    </net>
    <net code="4" name="Net-IN_MINUS">
      <node ref="U1" pin="2" pinfunction="IN_MINUS"/>
    </net>
    <net code="5" name="Net-OUT">
      <node ref="U1" pin="6" pinfunction="OUT"/>
    </net>
  </nets>
</export>
```

### Step 4: Add a test

Add `tests/test_lm741.py`:

```python
from kicad_circuit_ai.tools.validate import validate_from_netlist_path
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

def test_detects_v_minus_on_gnd():
    """V_MINUS on GND = split-supply op-amp wired for single supply incorrectly."""
    errors = validate_from_netlist_path(FIXTURES / "bad_741_single_supply.xml")
    codes = [e.code for e in errors]
    assert "WRONG_NET_CRITICAL" in codes

def test_lm741_aliases_recognized():
    """uA741 and LM741 should match the same knowledge base entry."""
    errors = validate_from_netlist_path(FIXTURES / "bad_741_single_supply.xml",
                                        component_override="uA741")
    assert any(e.component_value in ("LM741", "uA741") for e in errors)
```

### Step 5: Open a PR

```bash
git checkout -b feat/add-lm741
git add components/LM741.yaml tests/fixtures/bad_741_single_supply.xml tests/test_lm741.py
git commit -m "knowledge: add LM741 op-amp with split-supply validation"
gh pr create
```

---

## Pin field reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Pin name from datasheet |
| `function` | string | yes | Semantic function (see list below) |
| `type` | string | yes | KiCad pin type |
| `must_connect_to` | string | no | Net name this pin must be on |
| `must_not_be` | list[string] | no | Net names this pin must NOT be on |
| `warn_if_floating` | bool | no | Warn if pin is unconnected |
| `critical` | bool | no | Elevate to CRITICAL severity |
| `optional` | bool | no | Do not warn if floating |
| `notes` | string | no | Human-readable explanation for engineers |
| `recommended` | string | no | Recommended connection (e.g., "100nF bypass cap to GND") |
| `typically_connected_to` | string | no | Usually connected together (generates a hint) |

### Known function values

`ground`, `positive_supply`, `negative_supply`, `output`, `input`, `clock`, `reset`, `enable`, `chip_select`, `spi_mosi`, `spi_miso`, `spi_sck`, `i2c_sda`, `i2c_scl`, `uart_tx`, `uart_rx`, `analog_input`, `analog_output`, `pwm_output`, `trigger_input`, `threshold`, `discharge`, `control_voltage`, `offset_null`, `no_connect`

---

## What makes a good component YAML

- **Cover the common mistakes for your component.** Think about what a student in their first electronics course might wire wrong.
- **The `notes` field is for students,** not datasheets. Write "Connecting directly to GND holds the IC in permanent reset — use a pull-up resistor or tie to VCC when reset is not needed" rather than "Active low reset pin."
- **Aliases matter.** Students use `uA741`, `MC1741`, `LM741`. Include all common aliases.
- **`common_configurations` section is optional** but very helpful for well-known circuits (555 astable, 555 monostable, etc.).

---

## Good first issues

Search GitHub Issues for the `good first issue` label. These are typically:
- Adding a new component to the knowledge base
- Adding a Spanish translation for an error message
- Adding a test fixture for a common circuit topology

## Code of Conduct

Be kind. This project is for students learning electronics. Many contributors will be non-native English speakers.

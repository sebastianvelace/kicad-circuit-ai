# kicad-circuit-ai

[![CI](https://github.com/sebasvelace/kicad-circuit-ai/workflows/CI/badge.svg)](https://github.com/sebasvelace/kicad-circuit-ai/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/sebasvelace/kicad-circuit-ai/branch/main/graph/badge.svg)](https://codecov.io/gh/sebasvelace/kicad-circuit-ai)
[![PyPI](https://img.shields.io/pypi/v/kicad-circuit-ai.svg)](https://pypi.org/project/kicad-circuit-ai/)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Circuit Intelligence Layer for KiCad** — an MCP server that detects logic errors that KiCad ERC/DRC cannot see.

> My professor rejected my PCB. An AI diagnosed that 5 pins of my NE555 were shorted to ground. KiCad never warned me.
>
> — Sebas Velandia, Electronic Engineering student, UNAL

---

## Why this exists

KiCad's ERC checks *pin types* (power input, output, passive). It does **not** check whether your connections make electrical sense. If you connect VCC to GND, put RST in permanent reset, or skip your bypass capacitors, KiCad will happily export your Gerbers and you'll only find out when the board comes back from the fab and doesn't work.

This MCP server adds a **semantic validation layer**: it knows what each pin of a component is *supposed* to do, and tells you when your schematic violates that.

```
Input:  NE555 schematic — Pin 8 (VCC) connected to GND

Output: ❌ CRITICAL [U1 NE555] Pin 8 (VCC) is connected to GND.
           This is the positive supply pin of the IC.
           Connecting it to GND will prevent the circuit from working
           and may damage the component.
           Did you mean to connect Pin 1 (GND) instead?
```

---

## What this is NOT

This project **complements** existing KiCad MCP servers (like [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server)). It does not replace them. It adds a validation layer on top.

---

## Supported input formats

| Format | How to get it |
|--------|--------------|
| KiCad Netlist XML (`.net`) | KiCad → Tools → Generate Netlist → KiCad format |
| KiCad Schematic (`.kicad_sch`) | Your project file directly |

---

## MCP Tools

### `validate_circuit_logic`

```
validate_circuit_logic(schematic_path: str, locale: str = "en") -> str
```

Validates all components in a schematic against the component knowledge base. Returns a formatted report with errors and warnings.

**Example (Claude Code):**
```
Hey Claude, validate my schematic: validate_circuit_logic("/path/to/my_project.kicad_sch", locale="es")
```

### `explain_error`

```
explain_error(error_code: str, locale: str = "en") -> str
```

Returns a detailed human-readable explanation of a specific error code with educational context.

### `suggest_fix`

```
suggest_fix(component_value: str, pin_number: str, current_net: str) -> str
```

Suggests the correct connection for a mis-wired pin.

---

## Component knowledge base

The validator works because it knows what each pin of a component does. This knowledge lives in YAML files under `components/`:

```yaml
# components/NE555.yaml
pins:
  8:
    name: VCC
    function: positive_supply
    type: power_input
    must_connect_to: VCC
    must_not_be: [GND]     # ← This is the rule that catches your error
    critical: true
```

**Currently supported components:**

| Component | Category | File |
|-----------|----------|------|
| NE555 / LM555 | Timer | `NE555.yaml` |
| LM7805 | Voltage Regulator | `LM7805.yaml` |
| ATmega328P | Microcontroller | `ATmega328P.yaml` |
| LM741 | Op-Amp | `LM741.yaml` |
| L293D | Motor Driver | `L293D.yaml` |

**Want to add a component?** See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Setup

### Prerequisites

- Python 3.11+
- KiCad 7.x, 8.x, or 9.x

### Install with uv (recommended)

```bash
uvx kicad-circuit-ai
```

### Install with pip (venv)

```bash
git clone https://github.com/sebasvelace/kicad-circuit-ai
cd kicad-circuit-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configure in Claude Code

```bash
claude mcp add kicad-circuit-ai -- python3 -m kicad_circuit_ai.server
```

Or add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kicad-circuit-ai": {
      "command": "python3",
      "args": ["-m", "kicad_circuit_ai.server"],
      "env": {
        "KICAD_AI_COMPONENTS_DIR": "/path/to/kicad-circuit-ai/components"
      }
    }
  }
}
```

---

## Run tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_ne555.py::test_detects_vcc_on_gnd PASSED
tests/test_ne555.py::test_detects_rst_on_gnd PASSED
tests/test_ne555.py::test_detects_all_five_errors PASSED
tests/test_ne555.py::test_correct_555_passes PASSED
tests/test_validate.py::test_unknown_component_skipped PASSED
```

---

## The origin story (in Spanish)

Mi profesor rechazó mi Práctica 7. Al analizar los Gerbers, descubrí que 5 de los 8 pines del NE555 estaban conectados a GND: pin 2 (TRIG), pin 4 (RST), pin 5 (CV), pin 6 (THRS) y pin 8 (VCC). El circuito era físicamente imposible. KiCad no me avisó. El DRC pasó. Los Gerbers salieron perfectamente formateados de un diseño completamente roto.

Este proyecto existe para que eso no le pase a ningún otro estudiante de electrónica.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — adding a new component takes ~10 minutes.

## License

MIT — see [LICENSE](LICENSE)

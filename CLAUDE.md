# kicad-circuit-ai — Instructions for Claude Code

## What this project does

`kicad-circuit-ai` is a Python MCP server that validates KiCad schematics for logical errors (wrong net assignments, shorted power pins, missing bypass caps, floating resets). It complements existing KiCad MCP servers — it does NOT replace them.

## Project structure

```
src/kicad_circuit_ai/
├── server.py          # MCP entry point — FastMCP server with 3 tools
├── models.py          # Data classes: PinConnection, ComponentInstance, ValidationError
├── tools/
│   ├── validate.py    # validate_circuit_logic() — main validation engine
│   ├── explain.py     # explain_error() — human-readable explanations
│   └── suggest.py     # suggest_fix() — fix suggestions per pin
├── knowledge/
│   ├── loader.py      # Loads YAML files from components/ directory
│   └── rules.py       # Generic rules (VCC≠GND, floating resets, etc.)
├── parser/
│   ├── schematic.py   # Parses .kicad_sch using sexpdata
│   └── netlist.py     # Parses KiCad XML netlist (.net files)
└── i18n/
    ├── es.yaml        # Spanish error messages
    └── en.yaml        # English error messages
components/            # YAML knowledge base, one file per IC
tests/
├── test_ne555.py      # Tests using bad_555_netlist.xml fixture (the origin story)
├── test_validate.py   # Unit tests for validation logic
└── fixtures/
    ├── bad_555_netlist.xml   # Broken NE555 circuit (5 pins on GND)
    └── good_555_astable.xml  # Correct NE555 astable circuit
```

## Key conventions

- **Components directory**: The `KICAD_AI_COMPONENTS_DIR` env var overrides the default `components/` path relative to the package. Always use `knowledge/loader.py` to load components, never read YAML directly.
- **Locales**: `"en"` and `"es"` are supported. Default is `"en"`. All user-facing strings MUST have entries in both `i18n/en.yaml` and `i18n/es.yaml`.
- **Error severity**: Three levels — `CRITICAL` (circuit won't work), `ERROR` (likely broken), `WARNING` (might work but best practice violated).
- **Net name normalization**: GND, GND0, GNDA, EARTH, VSS, 0V are all treated as GND. VCC, VDD, +5V, +3V3, +3.3V, VBUS are treated as VCC-type. Use `knowledge/rules.py` for this.
- **Unknown components**: If a component is not in the knowledge base, skip silently with an info log. Never raise an error for unknown components.

## Adding a component to the knowledge base

1. Copy `components/NE555.yaml` as a template
2. Fill in pin definitions, `must_connect_to`, `must_not_be`, `warn_if_floating`
3. Add a test in `tests/` using an XML netlist fixture
4. See [CONTRIBUTING.md](CONTRIBUTING.md) for full instructions

## Running tests

```bash
# From project root, with venv activated
pytest tests/ -v
```

Tests do NOT require KiCad to be installed. They use XML netlist fixtures.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KICAD_AI_COMPONENTS_DIR` | `{package_root}/../../components` | Path to YAML component files |
| `KICAD_AI_LOG_LEVEL` | `WARNING` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `KICAD_AI_LOCALE` | `en` | Default locale for error messages |

## Dependency notes

- `sexpdata` must be available for `.kicad_sch` parsing. The existing KiCAD-MCP-Server also uses it.
- `mcp` (FastMCP) requires Python 3.11+.
- `pyyaml` for knowledge base loading.
- Tests have no external dependencies beyond `pytest`.

## Relation to KiCAD-MCP-Server

This project can be used standalone or alongside `mixelpixx/KiCAD-MCP-Server`. When used together, register both MCP servers in Claude Code — the validation tools appear alongside the routing/schematic tools seamlessly.

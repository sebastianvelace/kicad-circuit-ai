# Setup Guide

## Requirements

- Python 3.11 or higher
- KiCad 7.x / 8.x / 9.x (for generating files to validate)
- `pip` or `uv`

---

## Installation

### Option A: uv (fastest, recommended when available)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the server directly without cloning
uvx kicad-circuit-ai
```

### Option B: Clone + venv

```bash
git clone https://github.com/sebasvelace/kicad-circuit-ai
cd kicad-circuit-ai

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

### Option C: Claude Code MCP (most useful)

After cloning:

```bash
claude mcp add kicad-circuit-ai -- /path/to/.venv/bin/python3 -m kicad_circuit_ai.server
```

Or add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kicad-circuit-ai": {
      "command": "/path/to/.venv/bin/python3",
      "args": ["-m", "kicad_circuit_ai.server"],
      "env": {
        "KICAD_AI_COMPONENTS_DIR": "/path/to/kicad-circuit-ai/components",
        "KICAD_AI_LOCALE": "es"
      }
    }
  }
}
```

---

## Verify installation

```bash
pytest tests/ -v
```

All tests should pass without KiCad installed.

---

## Getting a netlist from KiCad

The most reliable input format is the KiCad XML netlist:

1. Open your project in KiCad
2. In the Schematic Editor: **Tools → Generate Netlist**
3. Select **KiCad** format
4. Save as `myproject.net`
5. Run: `validate_circuit_logic("/path/to/myproject.net")`

## Schematic files directly

You can also pass `.kicad_sch` files directly, but the parser only detects direct connections (power symbols placed exactly at pin endpoints). For circuits with wires between pins and power symbols, use the netlist method above.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KICAD_AI_COMPONENTS_DIR` | `components/` in package | Override component knowledge base path |
| `KICAD_AI_LOCALE` | `en` | Default language (`en` or `es`) |
| `KICAD_AI_LOG_LEVEL` | `WARNING` | Logging level |

---

## Troubleshooting

**"No components in knowledge base"**
→ Set `KICAD_AI_COMPONENTS_DIR` to the absolute path of the `components/` directory.

**"sexpdata not found"**
→ Install it: `pip install sexpdata`

**"mcp not found"**
→ Install it: `pip install mcp`

**"File not found"**
→ Use absolute paths, not relative. Double-check the path with `ls`.

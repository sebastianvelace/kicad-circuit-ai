# Roadmap

## v0.1 — MVP (current)

- [x] XML netlist parser (`.net` format from KiCad)
- [x] Schematic parser (`.kicad_sch`, direct connections)
- [x] YAML-based component knowledge base
- [x] `validate_circuit_logic` MCP tool
- [x] `explain_error` MCP tool
- [x] `suggest_fix` MCP tool
- [x] English + Spanish error messages
- [x] Components: NE555, LM7805, ATmega328P, LM741, L293D
- [x] Test suite (no KiCad required)

## v0.2 — Community + More Components

- [ ] 10 additional components (ESP32, STM32F103, LM317, NE5532, CD4017, ULN2003, L298N, MAX232, AMS1117, PCF8574)
- [ ] CONTRIBUTING.md automation: GitHub Action that validates new component YAML against schema
- [ ] `npx kicad-ai-setup` one-command installer
- [ ] Wire-tracing in `.kicad_sch` parser (beyond direct connections)

## v0.3 — Integration

- [ ] Proxy mode: compose with `mixelpixx/KiCAD-MCP-Server` tools in one session
- [ ] `check_before_export` hook: auto-validate before `export_gerber`
- [ ] HTML report output option
- [ ] Portuguese error messages

## v1.0 — Stable

- [ ] 25+ components in knowledge base
- [ ] Package published to PyPI
- [ ] `uvx kicad-circuit-ai` works without cloning
- [ ] Web-based schematic upload UI (optional)

---

## Component wishlist (vote by opening a GitHub issue)

These are the most-requested components from the community:

| Component | Category | Votes |
|-----------|----------|-------|
| ESP32 | Microcontroller | - |
| STM32F103 | Microcontroller | - |
| LM317 | Adjustable Regulator | - |
| L298N | Motor Driver | - |
| CD4017 | Decade Counter | - |
| ULN2003 | Darlington Array | - |
| MAX232 | RS-232 Driver | - |
| AMS1117 | LDO Regulator | - |
| PCF8574 | I2C I/O Expander | - |
| MCP23017 | I2C I/O Expander | - |

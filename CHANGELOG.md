# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-05-17

### Added

- Template system: `list_available_templates`, `copy_template_project`, `save_project_as_template`
- Pre-defined recipes: `555_monostable_recipe`, `lm7805_psu_recipe`
- BOM helper and MCP tool: `generate_bom_from_recipe`
- Repository infrastructure: MIT `LICENSE`, GitHub Actions CI, Codecov upload, issue templates, `.coveragerc`
- `CHANGELOG` and README badges

## [0.2.0] - 2025-05-01

### Added

- Package tools: `zip_gerbers`, `restrict_dsn_to_single_layer`
- Recipe discovery: `parse_circuit_from_description`, `get_pcb_workflow_recipe`
- Pre-defined `555_astable` workflow recipe (JSON)

## [0.1.0] - 2025-04-15

### Added

- Initial MCP server with semantic validation for NE555, LM7805, ATmega328P, LM741, L293D
- Knowledge-base YAML components and `validate_circuit_logic`, `explain_error`, `suggest_fix`, `list_known_components`

[0.3.0]: https://github.com/sebasvelace/kicad-circuit-ai/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sebasvelace/kicad-circuit-ai/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sebasvelace/kicad-circuit-ai/releases/tag/v0.1.0

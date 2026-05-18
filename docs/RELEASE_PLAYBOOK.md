# Playbook: de imagen o proyecto a PCB lista para fabricar

Este documento enlaza **kicad-circuit-ai** (validación, recetas, BOM, plan de release) con **KiCAD-MCP-Server** (esquema, PCB, ERC, DRC, export).

## Herramientas clave

| Paso | Servidor | Herramienta |
|------|-----------|-------------|
| Receta / caption | kicad-circuit-ai | `parse_circuit_from_description`, `get_pcb_workflow_recipe` |
| Plan ordenado | kicad-circuit-ai | `get_pcb_release_plan` |
| Lógica (VCC/GND, etc.) | kicad-circuit-ai | `validate_circuit_logic` |
| ERC | KiCAD-MCP-Server | `run_erc` |
| DRC | KiCAD-MCP-Server | `run_drc` (requiere proyecto/PCB cargado y guardado según tu flujo) |
| DFM básico | KiCAD-MCP-Server | `run_dfm_basic` |
| BOM desde receta | kicad-circuit-ai | `generate_bom_from_recipe` |
| Gerbers | KiCAD-MCP-Server | `export_gerber` |

## Ruta principiante (imagen → PCB)

1. Usuario sube imagen → modelo genera JSON según [image_to_recipe_prompt.md](./image_to_recipe_prompt.md).
2. Comprobar **fast path**: `list_available_templates()` → si existe, `copy_template_project` + `open_project` + colocación mínima si hace falta + `autoroute`.
3. Si no hay plantilla: `create_project` → `add_schematic_component` / cables según receta o JSON → `annotate_schematic` → `sync_schematic_to_board` → `add_board_outline` → `place_component` → `autoroute`.
4. **No exportar** hasta completar la **Puerta de release** (siguiente sección).

## Ruta experto (proyecto ya existente)

1. `open_project` con el `.kicad_pro`.
2. `validate_circuit_logic` sobre `.kicad_sch` o `.net` exportado.
3. Tras cambios en esquema: `sync_schematic_to_board`.
4. **Puerta de release** igual que abajo.
5. `export_gerber` (y zip/BOM según flujo).

## Puerta de release (obligatoria antes de Gerbers)

Ejecutar en orden (o usa la salida JSON de `get_pcb_release_plan`):

1. **Semantic** — `validate_circuit_logic(schematic_path o netlist)`. Si hay errores **críticos**, corregir antes de seguir.
2. **ERC** — `run_erc(schematicPath)`.
3. **DRC** — `run_drc` con el PCB correctamente cargado/guardado en el servidor KiCad (según documentación del MCP).
4. **DFM** — `run_dfm_basic(boardPath)` con ruta absoluta al `.kicad_pcb`.
5. **BOM** (opcional pero recomendado) — `generate_bom_from_recipe` si tienes JSON de receta; si no, `export_bom` en KiCAD-MCP.
6. **export_gerber** — solo si los pasos bloqueantes están en verde o aceptados explícitamente por el usuario.

## No exportar si…

| Condición | Acción |
|-----------|--------|
| `validate_circuit_logic` reporta errores críticos | Corregir esquema / nets. |
| ERC con violaciones **error** (no solo info) | Corregir según mensajes. |
| DRC con errores de diseño | Corregir pistas/huellas/reglas. |
| `run_dfm_basic` reporta solapes de courtyard (o categorías error en tu política) | Reubicar footprints o revisar huellas. |
| Pines sin conectar en DRC/ERC según política del proyecto | Documentar o corregir. |

## Referencias

- Contr imagen: [image_to_recipe_prompt.md](./image_to_recipe_prompt.md)
- Tool de plan: `get_pcb_release_plan` en el MCP kicad-circuit-ai

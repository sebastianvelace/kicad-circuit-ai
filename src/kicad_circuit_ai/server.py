"""MCP server entry point for kicad-circuit-ai.

Tools:
  - validate_circuit_logic: validate .net / .kicad_sch for logic errors
  - explain_error: educational explanation for an error code
  - suggest_fix: fix suggestion for a specific pin/net combination
  - list_known_components: list components in the knowledge base
  - zip_gerbers: compress a Gerber output folder into a .zip
  - restrict_dsn_to_single_layer: modify DSN for single-side Freerouting
  - parse_circuit_from_description: image description → structured recipe JSON
  - get_pcb_workflow_recipe: return a pre-defined circuit recipe by name
  - list_available_templates: list saved KiCad project templates
  - copy_template_project: copy a template to a working directory
  - save_project_as_template: save a completed project as a template
  - generate_bom_from_recipe: BOM from recipe JSON (csv / json / markdown)
"""

import os
from pathlib import Path


def _create_server():
    from mcp.server.fastmcp import FastMCP
    from kicad_circuit_ai.tools.validate import validate_from_file
    from kicad_circuit_ai.tools.explain import explain_error_code
    from kicad_circuit_ai.tools.suggest import suggest_fix as _suggest_fix
    from kicad_circuit_ai.knowledge.loader import ComponentKnowledgeBase

    mcp = FastMCP(
        "kicad-circuit-ai",
        instructions=(
            "I validate KiCad schematics for circuit logic errors — wrong net assignments, "
            "shorted power pins, floating resets, missing bypass caps. "
            "I work with .kicad_sch files and KiCad XML netlists (.net). "
            "I complement, not replace, existing KiCad MCP servers."
        ),
    )

    @mcp.tool()
    def validate_circuit_logic(schematic_path: str, locale: str = "en") -> str:
        """Validate a KiCad schematic or netlist for circuit logic errors.

        Detects errors that KiCad ERC/DRC cannot: wrong net assignments on critical pins
        (VCC→GND, RST→GND), floating control inputs, missing bypass capacitors.

        Args:
            schematic_path: Path to .kicad_sch schematic or .net KiCad netlist XML file.
            locale: Language for error messages. "en" (English) or "es" (Spanish).

        Returns:
            Formatted validation report with errors and suggestions.
        """
        path = Path(schematic_path)
        if not path.exists():
            return f"File not found: {schematic_path}"
        try:
            report = validate_from_file(path, locale=locale)
            return report.format(locale)
        except Exception as e:
            return f"Validation failed: {e}"

    @mcp.tool()
    def explain_error(error_code: str, locale: str = "en") -> str:
        """Return a detailed, educational explanation of a validation error code.

        Args:
            error_code: Error code from validate_circuit_logic output (e.g., "WRONG_NET_CRITICAL").
            locale: Language. "en" or "es".

        Returns:
            Detailed explanation with context about why this error matters.
        """
        return explain_error_code(error_code, locale)

    @mcp.tool()
    def suggest_fix(component_value: str, pin_number: str, current_net: str, locale: str = "en") -> str:
        """Suggest the correct connection for a mis-wired pin.

        Args:
            component_value: Component name (e.g., "NE555", "LM7805").
            pin_number: Pin number as string (e.g., "8" for VCC of NE555).
            current_net: The net the pin is currently on (e.g., "GND").
            locale: Language. "en" or "es".

        Returns:
            Human-readable fix suggestion with the correct connection.
        """
        return _suggest_fix(component_value, pin_number, current_net, locale)

    @mcp.tool()
    def list_known_components(locale: str = "en") -> str:
        """List all components in the knowledge base.

        Returns:
            List of component names that can be validated.
        """
        kb = ComponentKnowledgeBase()
        components = kb.list_components()
        if not components:
            return "No components in knowledge base." if locale == "en" else "No hay componentes en la base de conocimiento."
        header = f"Known components ({len(components)}):" if locale == "en" else f"Componentes conocidos ({len(components)}):"
        return header + "\n" + "\n".join(f"  • {c}" for c in components)

    from kicad_circuit_ai.tools.package import zip_gerbers as _zip_gerbers
    from kicad_circuit_ai.tools.package import restrict_dsn_to_single_layer as _restrict_dsn
    from kicad_circuit_ai.tools.circuit_parser import (
        parse_circuit_from_description as _parse_circuit,
        get_pcb_workflow_recipe as _get_recipe,
    )
    from kicad_circuit_ai.tools.bom import generate_bom_from_recipe as _generate_bom
    from kicad_circuit_ai.tools.template_manager import (
        copy_template_project as _copy_template,
        save_project_as_template as _save_template,
        list_available_templates as _list_templates,
    )

    @mcp.tool()
    def zip_gerbers(folder_path: str, output_zip: str = "") -> str:
        """Compress all Gerber and drill files in a folder into a ZIP archive.

        Call this after export_gerber to create a .zip ready for JLCPCB / PCBWay.

        Args:
            folder_path: Directory containing .gbr, .drl and related files.
            output_zip: Output ZIP path. Omit to auto-name (folder_gerbers.zip).

        Returns:
            Absolute path of the created ZIP file.
        """
        try:
            return _zip_gerbers(folder_path, output_zip or None)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def restrict_dsn_to_single_layer(dsn_path: str, layer: str = "F.Cu") -> str:
        """Modify a Freerouting DSN file to restrict routing to a single copper layer.

        Use this before running Freerouting to force single-sided routing.
        The DSN is exported by KiCad via export_dsn, modified here, then
        Freerouting runs on the modified DSN, and the result is imported via import_ses.

        Args:
            dsn_path: Path to the .dsn file exported by KiCad.
            layer: Copper layer to keep (default "F.Cu" for single-sided).

        Returns:
            Path of the modified DSN file.
        """
        try:
            return _restrict_dsn(dsn_path, layer)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def parse_circuit_from_description(description: str) -> str:
        """Convert a circuit description (from image analysis) into a structured recipe.

        When you analyze a circuit image, pass your description here.
        If it matches a known circuit (like "555 astable"), returns the complete
        pre-defined recipe with exact component values, footprints, and net connections.
        No guessing needed — execute the recipe directly with KiCAD-MCP-Server tools.

        Args:
            description: Your text description of the circuit image.
                         Example: "NE555 astable oscillator with R1=10k, R2=47k, C1=10uF"

        Returns:
            JSON string with components list, net connections, and PCB variant definitions.
        """
        return _parse_circuit(description)

    @mcp.tool()
    def get_pcb_workflow_recipe(circuit_type: str) -> str:
        """Return the complete PCB workflow recipe for a known circuit type.

        Use this to get the exact component values, footprints, nets, and
        PCB variant definitions for a circuit without analyzing an image.

        Args:
            circuit_type: Circuit name. Examples: "555_astable", "555 astable",
                          "555_monostable", "555 monostable", "lm7805_psu", "lm7805".

        Returns:
            JSON string with the full recipe, or an error listing available recipes.
        """
        return _get_recipe(circuit_type)

    @mcp.tool()
    def generate_bom_from_recipe(recipe_json: str, output_format: str = "csv") -> str:
        """Generate a Bill of Materials from a circuit recipe JSON string.

        Pass the JSON returned by get_pcb_workflow_recipe() or parse_circuit_from_description().
        Includes suggested LCSC part numbers for common passives and ICs.

        Args:
            recipe_json: Full recipe as a JSON string.
            output_format: ``csv`` (default), ``json``, or ``markdown`` (GitHub-flavored table).

        Returns:
            BOM text, or an error message if JSON is invalid.
        """
        return _generate_bom(recipe_json, output_format)

    @mcp.tool()
    def list_available_templates() -> str:
        """List available pre-built KiCad project templates.

        Call this FIRST before any PCB workflow to check if a fast path exists.
        If a template is available, use copy_template_project() to skip schematic
        building and component placement — go straight to open_project() + autoroute().

        Returns:
            JSON with {"templates": [...]} listing names usable with copy_template_project().
        """
        return _list_templates()

    @mcp.tool()
    def copy_template_project(circuit_type: str, dest_dir: str) -> str:
        """Copy a pre-built KiCad project template to a working directory.

        Fast path: skips create_project, add_schematic_component, add_wire,
        annotate_schematic, sync_schematic_to_board, and place_component.
        Go straight to open_project() then autoroute().

        Args:
            circuit_type: Template name (e.g., "555_astable").
                          Call list_available_templates() to see options.
            dest_dir: Directory where the project copy will be created.

        Returns:
            JSON with project_path, schematic_path, board_path ready for open_project().
        """
        try:
            return _copy_template(circuit_type, dest_dir)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def save_project_as_template(project_path: str, circuit_type: str) -> str:
        """Save a completed KiCad project as a reusable template for future runs.

        Call this ONCE after the first successful full PCB workflow (slow path).
        Saves the .kicad_pro + .kicad_sch + .kicad_pcb files as a template.
        Future runs call copy_template_project() instead of rebuilding from scratch,
        reducing tool calls by ~60%.

        Args:
            project_path: Path to the .kicad_pro file of the completed project.
            circuit_type: Template name to use (e.g., "555_astable").

        Returns:
            JSON with status, template_dir, and list of saved files.
        """
        try:
            return _save_template(project_path, circuit_type)
        except Exception as e:
            return f"Error: {e}"

    return mcp


def main():
    server = _create_server()
    server.run()


if __name__ == "__main__":
    main()

"""MCP server entry point for kicad-circuit-ai.

Registers three tools:
  - validate_circuit_logic: main validation, supports .net and .kicad_sch
  - explain_error: detailed educational explanation for an error code
  - suggest_fix: fix suggestion for a specific pin/net combination
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

    return mcp


def main():
    server = _create_server()
    server.run()


if __name__ == "__main__":
    main()

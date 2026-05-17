"""Parse a circuit description (text from Claude Vision) into a structured JSON recipe.

When Claude analyzes a circuit image, it produces a text description.
This module converts that description into the structured format that
KiCAD-MCP-Server tools expect — without any guessing by Claude.

Pre-defined recipes for common circuits are loaded from workflows/*.json.
If the description matches a known circuit, the recipe is returned directly,
saving tokens on back-and-forth clarification.
"""

import json
import re
from pathlib import Path
from typing import Optional

_WORKFLOWS_DIR = Path(__file__).parent.parent.parent.parent / "workflows"

_CIRCUIT_KEYWORDS: dict[str, list[str]] = {
    "555_astable": [
        "555 astable", "555 aestable", "555 aestável", "astable 555",
        "ne555 astable", "lm555 astable", "oscilador 555", "oscillator 555",
        "temporizador 555 astable", "timer 555 astable", "555 oscillator",
        "práctica 6", "practica 6", "practice 6",
    ],
    "555_monostable": [
        "555 monostable",
        "555 monoestable",
        "monostable 555",
        "ne555 monostable",
        "pulso único",
        "single pulse",
        "one-shot 555",
        "timer monostable",
        "temporizador monostable",
    ],
    "lm7805_psu": [
        "lm7805",
        "7805",
        "fuente 5v",
        "regulador 5v",
        "5v power supply",
        "regulador de voltaje",
        "voltage regulator 5v",
    ],
}


def _load_recipe(circuit_key: str) -> Optional[dict]:
    """Load a pre-defined recipe JSON from the workflows directory."""
    recipe_file = _WORKFLOWS_DIR / f"{circuit_key}_recipe.json"
    if recipe_file.exists():
        with open(recipe_file, encoding="utf-8") as f:
            return json.load(f)
    return None


def _detect_circuit_type(description: str) -> Optional[str]:
    """Detect which pre-defined circuit the description matches."""
    lower = description.lower()
    for circuit_key, keywords in _CIRCUIT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return circuit_key
    return None


def parse_circuit_from_description(description: str) -> str:
    """Parse a circuit description into a structured JSON recipe.

    If the description matches a known circuit (e.g., "555 astable"),
    returns the full pre-defined recipe as JSON. Otherwise returns a
    partially filled template asking Claude to fill in the gaps.

    Args:
        description: Text description of the circuit (typically from Claude Vision).

    Returns:
        JSON string with components, nets, and PCB variant definitions.
    """
    circuit_type = _detect_circuit_type(description)

    if circuit_type:
        recipe = _load_recipe(circuit_type)
        if recipe:
            recipe["_matched_from"] = circuit_type
            recipe["_input_description"] = description[:200]
            return json.dumps(recipe, indent=2, ensure_ascii=False)

    # No pre-defined recipe found — return a structured template
    template = {
        "_status": "no_recipe_found",
        "_input_description": description[:200],
        "_instructions": (
            "Pre-defined recipe not found. Fill in the components and nets below "
            "based on the circuit description, then use KiCAD-MCP-Server tools to build it."
        ),
        "circuit": "Unknown circuit",
        "supply_voltage": "5V",
        "components": [
            {
                "ref": "U1",
                "symbol": "FILL_IN (e.g. Timer:NE555)",
                "footprint": "FILL_IN",
                "value": "FILL_IN",
                "x": 30, "y": 25
            }
        ],
        "nets": [
            {"name": "VCC", "pins": ["FILL_IN"]},
            {"name": "GND", "pins": ["FILL_IN"]}
        ],
        "board_size_mm": {"width": 60, "height": 50},
        "pcb_variants": [
            {"name": "Doble Cara", "routing_layers": ["F.Cu", "B.Cu"], "copper_pour": None},
            {"name": "Una Cara", "routing_layers": ["F.Cu"], "copper_pour": None},
            {"name": "Una Cara + Copper Pour", "routing_layers": ["F.Cu"],
             "copper_pour": {"layer": "F.Cu", "net": "GND", "clearance": 0.3, "minWidth": 0.25}}
        ]
    }
    return json.dumps(template, indent=2, ensure_ascii=False)


def get_pcb_workflow_recipe(circuit_type: str) -> str:
    """Return the pre-defined PCB workflow recipe for a known circuit type.

    Args:
        circuit_type: One of "555_astable", "555_monostable", "lm7805_psu", etc.
                      Spaces are normalized (e.g. "555 astable", "lm7805 psu").

    Returns:
        JSON string with the complete recipe, or an error message.
    """
    # Normalize input
    normalized = circuit_type.lower().replace(" ", "_").replace("-", "_")
    # Try direct match
    recipe = _load_recipe(normalized)
    if recipe:
        return json.dumps(recipe, indent=2, ensure_ascii=False)

    # Try keyword detection
    detected = _detect_circuit_type(circuit_type)
    if detected:
        recipe = _load_recipe(detected)
        if recipe:
            return json.dumps(recipe, indent=2, ensure_ascii=False)

    available = [f.stem.replace("_recipe", "") for f in _WORKFLOWS_DIR.glob("*_recipe.json")]
    return json.dumps({
        "error": f"No recipe found for '{circuit_type}'",
        "available_recipes": available,
        "tip": "Use parse_circuit_from_description() to detect the circuit type automatically."
    }, indent=2)

"""Parse KiCad schematic (.kicad_sch) files into ComponentInstance objects.

Uses sexpdata to parse the S-expression format. This parser handles the
most common case: power symbols (GND, VCC) directly at pin endpoints.

For complex topologies (wires between pins and power symbols), use the
KiCad XML netlist format instead (parser/netlist.py) — it's authoritative.

Algorithm:
1. Parse lib_symbols → get pin offsets per component type
2. Parse power symbols → get {world_position: net_name} map
3. Parse symbol instances → compute world pin positions via symbol transform
4. Match pin world positions to power symbol positions (±0.01mm tolerance)
5. Parse wire graph → flood-fill to extend connectivity
6. Parse net labels → assign names to wire-connected pins
"""

import logging
import math
from pathlib import Path
from typing import Optional

from kicad_circuit_ai.models import ComponentInstance, PinConnection

logger = logging.getLogger(__name__)

_TOLERANCE_MM = 0.01  # coordinate match tolerance in mm


def _try_import_sexpdata():
    try:
        import sexpdata
        return sexpdata
    except ImportError:
        return None


def _sym(name: str):
    """Return a sexpdata Symbol for comparison."""
    sexpdata = _try_import_sexpdata()
    if sexpdata is None:
        raise ImportError("sexpdata is required to parse .kicad_sch files. Install it with: pip install sexpdata")
    return sexpdata.Symbol(name)


def _find_children(sexp: list, tag: str) -> list:
    """Find all direct children of sexp that start with Symbol(tag)."""
    results = []
    sym = _sym(tag)
    for item in sexp:
        if isinstance(item, list) and item and item[0] == sym:
            results.append(item)
    return results


def _find_first(sexp: list, tag: str) -> Optional[list]:
    children = _find_children(sexp, tag)
    return children[0] if children else None


def _get_str(sexp: list, tag: str) -> str:
    found = _find_first(sexp, tag)
    if found and len(found) > 1:
        return str(found[1]).strip('"')
    return ""


def _rotate_point(x: float, y: float, angle_deg: float) -> tuple[float, float]:
    """Rotate point (x, y) around origin by angle_deg degrees (CCW)."""
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)


def _parse_lib_symbols(sexp: list) -> dict[str, list[dict]]:
    """Extract pin definitions from lib_symbols section.

    Returns {lib_id: [{"number": "1", "name": "GND", "x": 0.0, "y": -5.08}, ...]}
    """
    pins_by_lib: dict[str, list[dict]] = {}
    lib_syms = _find_first(sexp, "lib_symbols")
    if not lib_syms:
        return pins_by_lib

    for sym_def in lib_syms[1:]:
        if not isinstance(sym_def, list) or not sym_def:
            continue
        lib_id = str(sym_def[1]).strip('"')
        all_pins: list[dict] = []

        # KiCad nests actual pin defs inside sub-symbol units like (symbol "NAME_1_1" ...)
        for sub in sym_def:
            if not isinstance(sub, list) or not sub or str(sub[0]) != "symbol":
                continue
            for pin_def in sub:
                if not isinstance(pin_def, list) or not pin_def or str(pin_def[0]) != "pin":
                    continue
                # (pin TYPE GRAPHIC (at X Y ANGLE) (length L) (name ...) (number ...))
                at = _find_first(pin_def, "at")
                if not at or len(at) < 3:
                    continue
                pin_x = float(at[1])
                pin_y = float(at[2])
                pin_num = ""
                pin_name = ""
                num_el = _find_first(pin_def, "number")
                if num_el and len(num_el) > 1:
                    pin_num = str(num_el[1]).strip('"')
                name_el = _find_first(pin_def, "name")
                if name_el and len(name_el) > 1:
                    pin_name = str(name_el[1]).strip('"')
                if pin_num:
                    all_pins.append({"number": pin_num, "name": pin_name, "x": pin_x, "y": pin_y})

        if all_pins:
            pins_by_lib[lib_id] = all_pins

    return pins_by_lib


def _parse_power_positions(sexp: list) -> dict[tuple[float, float], str]:
    """Find all power symbols and return {(x, y): net_name}."""
    power_pos: dict[tuple[float, float], str] = {}

    for item in sexp:
        if not isinstance(item, list) or not item or str(item[0]) != "symbol":
            continue
        lib_id = ""
        for sub in item:
            if isinstance(sub, list) and sub and str(sub[0]) == "lib_id":
                lib_id = str(sub[1]).strip('"')
                break
        # Power symbols have lib_id like "power:GND" or "power:VCC"
        if not lib_id.startswith("power:"):
            continue
        net_name = lib_id.split(":", 1)[1]
        at = _find_first(item, "at")
        if at and len(at) >= 3:
            x, y = float(at[1]), float(at[2])
            power_pos[(x, y)] = net_name

    return power_pos


def _parse_net_labels(sexp: list) -> dict[tuple[float, float], str]:
    """Find all net labels and return {(x, y): label_name}."""
    labels: dict[tuple[float, float], str] = {}
    for label_type in ("label", "global_label", "hierarchical_label"):
        for item in sexp:
            if not isinstance(item, list) or not item or str(item[0]) != label_type:
                continue
            name = str(item[1]).strip('"') if len(item) > 1 else ""
            at = _find_first(item, "at")
            if at and len(at) >= 3 and name:
                labels[(float(at[1]), float(at[2]))] = name
    return labels


def _points_match(p1: tuple[float, float], p2: tuple[float, float]) -> bool:
    return abs(p1[0] - p2[0]) <= _TOLERANCE_MM and abs(p1[1] - p2[1]) <= _TOLERANCE_MM


def _find_net_at(pos: tuple[float, float], power_pos: dict, label_pos: dict) -> Optional[str]:
    for ppos, net in power_pos.items():
        if _points_match(pos, ppos):
            return net
    for lpos, net in label_pos.items():
        if _points_match(pos, lpos):
            return net
    return None


def parse_schematic(path: Path) -> list[ComponentInstance]:
    """Parse a .kicad_sch file and return component instances with pin net assignments.

    Note: This parser handles direct connections (pin endpoint == power/label position).
    It does not trace wires. For wire-connected nets, export a KiCad netlist XML first.
    """
    sexpdata = _try_import_sexpdata()
    if sexpdata is None:
        raise ImportError("sexpdata is required for .kicad_sch parsing")

    with open(path, encoding="utf-8") as f:
        content = f.read()
    sexp = sexpdata.loads(content)

    lib_pins = _parse_lib_symbols(sexp)
    power_pos = _parse_power_positions(sexp)
    label_pos = _parse_net_labels(sexp)

    instances: list[ComponentInstance] = []

    for item in sexp:
        if not isinstance(item, list) or not item or str(item[0]) != "symbol":
            continue
        lib_id = ""
        for sub in item:
            if isinstance(sub, list) and sub and str(sub[0]) == "lib_id":
                lib_id = str(sub[1]).strip('"')
                break
        if lib_id.startswith("power:"):
            continue

        at = _find_first(item, "at")
        if not at or len(at) < 3:
            continue
        sym_x, sym_y = float(at[1]), float(at[2])
        sym_angle = float(at[3]) if len(at) > 3 else 0.0

        ref = ""
        value = ""
        for sub in item:
            if not isinstance(sub, list) or len(sub) < 2 or str(sub[0]) != "property":
                continue
            prop_name = str(sub[1]).strip('"')
            prop_val = str(sub[2]).strip('"') if len(sub) > 2 else ""
            if prop_name == "Reference":
                ref = prop_val
            elif prop_name == "Value":
                value = prop_val

        if not ref or not value:
            continue

        pin_defs = lib_pins.get(lib_id, [])
        pins: list[PinConnection] = []
        for pin_def in pin_defs:
            rx, ry = _rotate_point(pin_def["x"], -pin_def["y"], -sym_angle)
            world_x = sym_x + rx
            world_y = sym_y + ry
            net = _find_net_at((world_x, world_y), power_pos, label_pos)
            pins.append(PinConnection(
                pin_number=pin_def["number"],
                pin_name=pin_def["name"],
                net_name=net or "UNCONNECTED",
                component_ref=ref,
                component_value=value,
            ))

        instances.append(ComponentInstance(ref=ref, value=value, lib_id=lib_id, pins=pins))

    return instances

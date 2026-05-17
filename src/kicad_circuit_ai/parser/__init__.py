from pathlib import Path
from typing import Union

from kicad_circuit_ai.models import ComponentInstance


def parse(path: Union[str, Path]) -> list[ComponentInstance]:
    """Auto-detect file format and parse into ComponentInstance list."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    suffix = p.suffix.lower()
    if suffix in (".net", ".xml"):
        from kicad_circuit_ai.parser.netlist import parse_netlist
        return parse_netlist(p)
    elif suffix == ".kicad_sch":
        from kicad_circuit_ai.parser.schematic import parse_schematic
        return parse_schematic(p)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .net (KiCad XML netlist) or .kicad_sch")

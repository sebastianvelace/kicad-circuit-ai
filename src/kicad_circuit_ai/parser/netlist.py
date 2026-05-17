"""Parse KiCad XML netlist (.net) files into ComponentInstance / PinConnection objects.

KiCad generates this file via: Tools → Generate Netlist → KiCad format (XML).

Format reference:
  <export version="D">
    <components>
      <comp ref="U1">
        <value>NE555</value>
        <libsource lib="Timer" part="NE555"/>
      </comp>
    </components>
    <nets>
      <net code="1" name="GND">
        <node ref="U1" pin="1" pinfunction="GND" pintype="power_in"/>
      </net>
    </nets>
  </export>
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from kicad_circuit_ai.models import ComponentInstance, PinConnection


def parse_netlist(path: Path) -> list[ComponentInstance]:
    """Parse a KiCad XML netlist and return component instances with their net assignments."""
    tree = ET.parse(path)
    root = tree.getroot()

    # Build component value map: ref → {value, lib_id}
    comp_meta: dict[str, dict] = {}
    for comp in root.findall(".//components/comp"):
        ref = comp.get("ref", "")
        value_el = comp.find("value")
        value = value_el.text.strip() if value_el is not None and value_el.text else ""
        libsource = comp.find("libsource")
        lib = libsource.get("lib", "") if libsource is not None else ""
        part = libsource.get("part", "") if libsource is not None else ""
        lib_id = f"{lib}:{part}" if lib and part else part or value
        comp_meta[ref] = {"value": value, "lib_id": lib_id}

    # Build pin→net map: ref → pin_num → {net_name, pin_function, pin_type}
    pin_nets: dict[str, dict[str, dict]] = {}
    for net_el in root.findall(".//nets/net"):
        net_name = net_el.get("name", "")
        for node in net_el.findall("node"):
            ref = node.get("ref", "")
            pin_num = node.get("pin", "")
            pin_func = node.get("pinfunction", "")
            if ref not in pin_nets:
                pin_nets[ref] = {}
            pin_nets[ref][pin_num] = {"net_name": net_name, "pin_function": pin_func}

    # Assemble ComponentInstance objects
    instances: list[ComponentInstance] = []
    for ref, meta in comp_meta.items():
        pins: list[PinConnection] = []
        for pin_num, pin_data in pin_nets.get(ref, {}).items():
            pins.append(PinConnection(
                pin_number=pin_num,
                pin_name=pin_data["pin_function"],
                net_name=pin_data["net_name"],
                component_ref=ref,
                component_value=meta["value"],
            ))
        instances.append(ComponentInstance(
            ref=ref,
            value=meta["value"],
            lib_id=meta["lib_id"],
            pins=pins,
        ))

    return instances

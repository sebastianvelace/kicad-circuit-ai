"""Tests for release_plan tool."""

import json
from pathlib import Path

from kicad_circuit_ai.tools.release_plan import build_release_plan, release_plan_json


def test_release_plan_order_and_tools():
    data = build_release_plan(None, None)
    tools = [s["tool"] for s in data["steps"]]
    assert tools == [
        "validate_circuit_logic",
        "run_erc",
        "run_drc",
        "run_dfm_basic",
        "generate_bom_from_recipe",
        "export_gerber",
    ]
    assert data["steps"][2]["server"] == "KiCAD-MCP-Server"
    assert data["steps"][2]["tool"] == "run_drc"


def test_release_plan_json_roundtrip():
    raw = release_plan_json("", "")
    data = json.loads(raw)
    assert data["version"] == 1
    assert len(data["steps"]) == 6


def test_release_plan_with_paths(tmp_path):
    sch = tmp_path / "x.kicad_sch"
    sch.write_text("(kicad_sch (version 20231120))\n")
    brd = tmp_path / "x.kicad_pcb"
    brd.write_text("(kicad_pcb (version 20231120))\n")

    data = build_release_plan(str(sch), str(brd))
    assert data["schematic_path"] == str(sch)
    v = next(s for s in data["steps"] if s["tool"] == "validate_circuit_logic")
    assert v["blocking"] is True
    er = next(s for s in data["steps"] if s["tool"] == "run_erc")
    assert er["args"]["schematicPath"] == str(sch)
    assert er["blocking"] is True
    dfm = next(s for s in data["steps"] if s["tool"] == "run_dfm_basic")
    assert dfm["args"]["boardPath"] == str(Path(brd).resolve())
    assert dfm["blocking"] is True

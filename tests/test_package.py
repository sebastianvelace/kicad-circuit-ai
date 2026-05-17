"""Tests for package.py (zip_gerbers, restrict_dsn) and circuit_parser.py."""

import json
import zipfile
from pathlib import Path

import pytest

from kicad_circuit_ai.tools.package import zip_gerbers, restrict_dsn_to_single_layer
from kicad_circuit_ai.tools.circuit_parser import (
    parse_circuit_from_description,
    get_pcb_workflow_recipe,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ── zip_gerbers ─────────────────────────────────────────────────────────────

@pytest.fixture
def gerber_folder(tmp_path):
    """Create a fake Gerber output folder."""
    folder = tmp_path / "gerbers_test"
    folder.mkdir()
    (folder / "circuit.gtl").write_text("G04 top copper*\n")
    (folder / "circuit.gbl").write_text("G04 bottom copper*\n")
    (folder / "circuit.gbr").write_text("G04 edge cuts*\n")
    (folder / "circuit.drl").write_text("M48\n")
    return folder


def test_zip_gerbers_creates_file(gerber_folder, tmp_path):
    out = tmp_path / "output.zip"
    result = zip_gerbers(str(gerber_folder), str(out))
    assert Path(result).exists()
    assert result.endswith(".zip")


def test_zip_gerbers_default_name(gerber_folder):
    result = zip_gerbers(str(gerber_folder))
    assert Path(result).exists()
    assert "gerbers_test" in result


def test_zip_gerbers_contains_gerber_files(gerber_folder, tmp_path):
    out = tmp_path / "out.zip"
    zip_gerbers(str(gerber_folder), str(out))
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    assert "circuit.gtl" in names
    assert "circuit.gbl" in names


def test_zip_gerbers_includes_drill(gerber_folder, tmp_path):
    out = tmp_path / "out.zip"
    zip_gerbers(str(gerber_folder), str(out))
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    assert "circuit.drl" in names


def test_zip_gerbers_folder_not_found():
    with pytest.raises(FileNotFoundError):
        zip_gerbers("/nonexistent/path/gerbers")


def test_zip_gerbers_empty_folder(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="No files"):
        zip_gerbers(str(empty))


# ── restrict_dsn_to_single_layer ────────────────────────────────────────────

@pytest.fixture
def sample_dsn(tmp_path):
    dsn_content = """\
(pcb
  (structure
    (layer "F.Cu" (type signal) (direction horizontal))
    (layer "B.Cu" (type signal) (direction vertical))
    (layer "In1.Cu" (type signal) (direction horizontal))
    (boundary (rect pcb 0 0 60000000 50000000))
  )
  (placement)
  (library)
  (network)
  (wiring)
)
"""
    dsn_file = tmp_path / "test.dsn"
    dsn_file.write_text(dsn_content)
    return dsn_file


def test_restrict_dsn_removes_b_cu(sample_dsn):
    restrict_dsn_to_single_layer(str(sample_dsn), layer="F.Cu")
    content = sample_dsn.read_text()
    assert "F.Cu" in content
    assert 'layer "B.Cu"' not in content or '; removed layer B.Cu' in content


def test_restrict_dsn_keeps_target_layer(sample_dsn):
    restrict_dsn_to_single_layer(str(sample_dsn), layer="F.Cu")
    content = sample_dsn.read_text()
    assert '"F.Cu"' in content


def test_restrict_dsn_to_b_cu(sample_dsn):
    """Should keep B.Cu and remove F.Cu when B.Cu is the target."""
    restrict_dsn_to_single_layer(str(sample_dsn), layer="B.Cu")
    content = sample_dsn.read_text()
    assert '"B.Cu"' in content
    assert 'layer "F.Cu"' not in content or '; removed layer F.Cu' in content


def test_restrict_dsn_writes_to_output_path(sample_dsn, tmp_path):
    out = tmp_path / "modified.dsn"
    result = restrict_dsn_to_single_layer(str(sample_dsn), layer="F.Cu", output_path=str(out))
    assert Path(result).exists()
    assert out.read_text() != ""


def test_restrict_dsn_file_not_found():
    with pytest.raises(FileNotFoundError):
        restrict_dsn_to_single_layer("/nonexistent/file.dsn")


# ── parse_circuit_from_description ──────────────────────────────────────────

def test_parse_555_astable_detected():
    result = parse_circuit_from_description("NE555 astable oscillator with R1=10k R2=47k C1=10uF")
    data = json.loads(result)
    assert data.get("_matched_from") == "555_astable"
    assert "components" in data
    assert "nets" in data


def test_parse_555_astable_spanish():
    result = parse_circuit_from_description("circuito 555 astable con resistencias de 10k y 47k")
    data = json.loads(result)
    assert data.get("_matched_from") == "555_astable"


def test_parse_555_astable_contains_ne555_component():
    result = parse_circuit_from_description("555 astable circuit")
    data = json.loads(result)
    refs = [c["ref"] for c in data["components"]]
    assert "U1" in refs
    u1 = next(c for c in data["components"] if c["ref"] == "U1")
    assert "NE555" in u1["symbol"] or "NE555" in u1["value"]


def test_parse_555_astable_has_vcc_gnd():
    result = parse_circuit_from_description("555 astable")
    data = json.loads(result)
    net_names = [n["name"] for n in data["nets"]]
    assert "VCC" in net_names
    assert "GND" in net_names


def test_parse_555_astable_has_pcb_variants():
    result = parse_circuit_from_description("555 astable")
    data = json.loads(result)
    assert "pcb_variants" in data
    assert len(data["pcb_variants"]) == 3


def test_parse_practica_6_matches():
    """'Práctica 6' should map to the 555 astable recipe."""
    result = parse_circuit_from_description("diseñar la PCB de la Práctica 6")
    data = json.loads(result)
    assert data.get("_matched_from") == "555_astable"


def test_parse_unknown_circuit_returns_template():
    result = parse_circuit_from_description("some completely unknown XYZ-9999 circuit")
    data = json.loads(result)
    assert data["_status"] == "no_recipe_found"
    assert "components" in data


# ── get_pcb_workflow_recipe ──────────────────────────────────────────────────

def test_get_recipe_555_astable():
    result = get_pcb_workflow_recipe("555_astable")
    data = json.loads(result)
    assert "components" in data
    assert data["circuit"] == "NE555 Astable Oscillator"


def test_get_recipe_with_spaces():
    result = get_pcb_workflow_recipe("555 astable")
    data = json.loads(result)
    assert "components" in data


def test_get_recipe_unknown_lists_available():
    result = get_pcb_workflow_recipe("unknown_circuit_xyz")
    data = json.loads(result)
    assert "error" in data
    assert "available_recipes" in data


def test_get_recipe_has_three_variants():
    result = get_pcb_workflow_recipe("555_astable")
    data = json.loads(result)
    variants = data["pcb_variants"]
    assert len(variants) == 3
    layer_configs = [v["routing_layers"] for v in variants]
    assert ["F.Cu", "B.Cu"] in layer_configs      # doble cara
    assert ["F.Cu"] in layer_configs               # una cara
    copper_pours = [v["copper_pour"] for v in variants]
    assert any(cp is not None for cp in copper_pours)  # copper pour variant exists

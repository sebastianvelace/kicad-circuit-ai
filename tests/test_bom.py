"""Tests for BOM generation from recipe JSON."""

import csv
import io
import json

import pytest

from kicad_circuit_ai.tools.bom import generate_bom_from_recipe
from kicad_circuit_ai.tools.circuit_parser import get_pcb_workflow_recipe


@pytest.fixture
def astable_recipe_json():
    return get_pcb_workflow_recipe("555_astable")


def test_bom_csv_headers_and_ne555_lcsc(astable_recipe_json):
    out = generate_bom_from_recipe(astable_recipe_json, "csv")
    reader = csv.DictReader(io.StringIO(out))
    rows = list(reader)
    fieldnames = reader.fieldnames
    assert fieldnames == ["Ref", "Value", "Footprint", "Qty", "LCSC_Part", "Description"]
    by_ref = {row["Ref"]: row for row in rows}
    assert "U1" in by_ref
    assert by_ref["U1"]["LCSC_Part"] == "C46749"
    # One row per distinct (symbol, value, footprint)
    u1_row = by_ref["U1"]
    assert u1_row["Qty"] == "1"


def test_bom_json_roundtrip(astable_recipe_json):
    raw = generate_bom_from_recipe(astable_recipe_json, "json")
    rows = json.loads(raw)
    assert isinstance(rows, list)
    u1 = next(r for r in rows if r["Ref"] == "U1")
    assert u1["LCSC_Part"] == "C46749"


def test_bom_markdown_table(astable_recipe_json):
    md = generate_bom_from_recipe(astable_recipe_json, "markdown")
    assert md.startswith("| Ref |")
    assert "C46749" in md


def test_bom_invalid_json():
    err = generate_bom_from_recipe("{not json", "csv")
    assert err.startswith("Error:")


def test_bom_invalid_format(astable_recipe_json):
    err = generate_bom_from_recipe(astable_recipe_json, "xml")
    assert "output_format" in err


def test_bom_monostable_has_47k_lcsc():
    recipe = get_pcb_workflow_recipe("555_monostable")
    out = generate_bom_from_recipe(recipe, "csv")
    assert "C25819" in out
    assert "47k" in out


def test_bom_lm7805_has_regulator_and_diode_lcsc():
    recipe = get_pcb_workflow_recipe("lm7805_psu")
    out = generate_bom_from_recipe(recipe, "csv")
    assert "C55509" in out
    assert "C14526" in out

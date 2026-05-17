"""Tests for NE555 validation — the origin story circuit.

The fixture bad_555_netlist.xml represents Practica-7: an NE555 where
5 of 8 pins were accidentally wired to GND. KiCad ERC/DRC did not catch this.
These tests verify that kicad-circuit-ai does.
"""

from pathlib import Path

import pytest

from kicad_circuit_ai.knowledge.loader import ComponentKnowledgeBase
from kicad_circuit_ai.models import Severity
from kicad_circuit_ai.parser.netlist import parse_netlist
from kicad_circuit_ai.tools.validate import validate_components, validate_from_netlist_path

FIXTURES = Path(__file__).parent / "fixtures"
COMPONENTS = Path(__file__).parent.parent / "components"


@pytest.fixture
def kb():
    return ComponentKnowledgeBase(components_dir=COMPONENTS)


@pytest.fixture
def bad_555_components():
    return parse_netlist(FIXTURES / "bad_555_netlist.xml")


@pytest.fixture
def good_555_components():
    return parse_netlist(FIXTURES / "good_555_astable.xml")


# --- The 5 errors from Practica-7 ---

def test_detects_vcc_on_gnd(bad_555_components, kb):
    """Pin 8 (VCC) on GND must be CRITICAL."""
    report = validate_components(bad_555_components, kb)
    vcc_errors = [e for e in report.errors if e.pin_number == "8" and e.component_ref == "U1"]
    assert vcc_errors, "Expected a CRITICAL error for Pin 8 (VCC) on GND"
    assert vcc_errors[0].severity == Severity.CRITICAL
    assert "GND" in vcc_errors[0].net_name


def test_detects_rst_on_gnd(bad_555_components, kb):
    """Pin 4 (RST) on GND — chip is permanently held in reset."""
    report = validate_components(bad_555_components, kb)
    rst_errors = [e for e in report.errors if e.pin_number == "4" and e.component_ref == "U1"]
    assert rst_errors, "Expected an error for Pin 4 (RST) on GND"


def test_detects_trig_on_gnd(bad_555_components, kb):
    """Pin 2 (TRIG) on GND — output permanently HIGH."""
    report = validate_components(bad_555_components, kb)
    trig_errors = [e for e in report.errors if e.pin_number == "2" and e.component_ref == "U1"]
    assert trig_errors, "Expected an error for Pin 2 (TRIG) on GND"


def test_detects_thrs_issue(bad_555_components, kb):
    """Pin 6 (THRS) on GND — capacitor never charges past threshold."""
    report = validate_components(bad_555_components, kb)
    thrs_issues = [e for e in report.errors if e.pin_number == "6" and e.component_ref == "U1"]
    assert thrs_issues, "Expected an error or warning for Pin 6 (THRS) on GND"


def test_detects_all_five_errors(bad_555_components, kb):
    """All 5 broken pins must generate at least one error each."""
    report = validate_components(bad_555_components, kb)
    broken_pins = {"2", "4", "8"}  # confirmed critical pins
    reported_pins = {e.pin_number for e in report.errors if e.component_ref == "U1"}
    for pin in broken_pins:
        assert pin in reported_pins, f"Expected error for Pin {pin} but none was generated"


def test_error_count_matches_problems(bad_555_components, kb):
    """At minimum 3 CRITICAL/ERROR issues for U1 (pins 4, 8, and RST)."""
    report = validate_components(bad_555_components, kb)
    critical_and_errors = [
        e for e in report.errors
        if e.component_ref == "U1" and e.severity in (Severity.CRITICAL, Severity.ERROR)
    ]
    assert len(critical_and_errors) >= 3, (
        f"Expected at least 3 critical/error issues, got {len(critical_and_errors)}: "
        f"{[e.pin_number for e in critical_and_errors]}"
    )


# --- Correct circuit should pass ---

def test_correct_555_has_no_critical_errors(good_555_components, kb):
    """A correctly wired NE555 astable circuit should not generate CRITICAL errors."""
    report = validate_components(good_555_components, kb)
    criticals = [e for e in report.errors if e.severity == Severity.CRITICAL]
    assert not criticals, (
        f"Correct 555 circuit should have no CRITICAL errors. Got: {[e.message_en for e in criticals]}"
    )


def test_correct_555_vcc_pin_passes(good_555_components, kb):
    """Pin 8 (VCC) on VCC net: must not generate any error."""
    report = validate_components(good_555_components, kb)
    vcc_errors = [e for e in report.errors if e.pin_number == "8" and e.component_ref == "U1"]
    assert not vcc_errors, f"VCC correctly wired but got errors: {[e.message_en for e in vcc_errors]}"


# --- Spanish locale ---

def test_error_message_in_spanish(bad_555_components, kb):
    """Error messages must be available in Spanish."""
    report = validate_components(bad_555_components, kb)
    vcc_errors = [e for e in report.errors if e.pin_number == "8"]
    assert vcc_errors, "Should have errors for VCC pin"
    spanish_msg = vcc_errors[0].message_es
    assert spanish_msg, "Spanish message must not be empty"
    assert len(spanish_msg) > 10, "Spanish message seems too short"


def test_report_format_spanish(bad_555_components, kb):
    """Full report formatted in Spanish should not contain untranslated strings."""
    report = validate_components(bad_555_components, kb)
    formatted = report.format(locale="es")
    assert "problema" in formatted.lower() or "encontr" in formatted.lower(), (
        "Spanish report should contain Spanish text"
    )


# --- Knowledge base ---

def test_ne555_in_knowledge_base(kb):
    """NE555 must be loadable from the knowledge base."""
    entry = kb.find("NE555")
    assert entry is not None, "NE555 not found in knowledge base"
    assert "pins" in entry


def test_ne555_alias_lm555(kb):
    """LM555 is an alias of NE555 and should resolve to the same entry."""
    entry = kb.find("LM555")
    assert entry is not None, "LM555 alias not found"
    assert entry["component"]["name"] == "NE555"


def test_ne555_variant_suffix(kb):
    """NE555P (with suffix) should match NE555."""
    entry = kb.find("NE555P")
    assert entry is not None, "NE555P variant not found"

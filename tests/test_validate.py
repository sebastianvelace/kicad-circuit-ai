"""Unit tests for the validation engine and knowledge base."""

from pathlib import Path

import pytest

from kicad_circuit_ai.knowledge.loader import ComponentKnowledgeBase
from kicad_circuit_ai.knowledge.rules import (
    is_gnd,
    is_vcc,
    is_floating,
    net_matches,
    normalize_net,
)
from kicad_circuit_ai.models import ComponentInstance, PinConnection, Severity
from kicad_circuit_ai.tools.validate import validate_components

COMPONENTS = Path(__file__).parent.parent / "components"


@pytest.fixture
def kb():
    return ComponentKnowledgeBase(components_dir=COMPONENTS)


# --- Net normalization ---

def test_gnd_variants():
    for net in ("GND", "GND0", "GNDA", "DGND", "VSS", "0V", "EARTH"):
        assert is_gnd(net), f"{net} should be recognized as GND"


def test_vcc_variants():
    for net in ("VCC", "VDD", "+5V", "+3V3", "+3.3V", "VBUS", "AVCC"):
        assert is_vcc(net), f"{net} should be recognized as VCC"


def test_floating_detection():
    for net in ("", "UNCONNECTED", "NC", "~", "?"):
        assert is_floating(net), f"'{net}' should be detected as floating"


def test_net_matches_normalized():
    assert net_matches("+5V", "VCC")
    assert net_matches("VSS", "GND")
    assert not net_matches("+5V", "GND")


def test_custom_net_not_normalized():
    assert not is_gnd("NET-GPIO0")
    assert not is_vcc("NET-GPIO0")


# --- Unknown component handling ---

def test_unknown_component_produces_no_error(kb):
    """Components not in the knowledge base should be silently skipped."""
    components = [
        ComponentInstance(
            ref="U99",
            value="SOME_UNKNOWN_IC_XYZ",
            lib_id="SomeLib:SomeIC",
            pins=[
                PinConnection("1", "VCC", "GND", "U99", "SOME_UNKNOWN_IC_XYZ"),
            ],
        )
    ]
    report = validate_components(components, kb)
    assert not report.errors, "Unknown components must not generate errors"
    assert "U99(SOME_UNKNOWN_IC_XYZ)" in report.unknown_components


# --- LM7805 validation ---

def test_lm7805_input_on_gnd(kb):
    """LM7805 IN pin on GND is critical."""
    components = [
        ComponentInstance(
            ref="U1",
            value="LM7805",
            lib_id="Regulator_Linear:LM7805",
            pins=[
                PinConnection("1", "IN", "GND", "U1", "LM7805"),
                PinConnection("2", "GND", "GND", "U1", "LM7805"),
                PinConnection("3", "OUT", "Net-OUT", "U1", "LM7805"),
            ],
        )
    ]
    report = validate_components(components, kb)
    in_errors = [e for e in report.errors if e.pin_number == "1"]
    assert in_errors, "IN pin on GND should generate an error"
    assert in_errors[0].severity in (Severity.CRITICAL, Severity.ERROR)


def test_lm7805_correct_wiring_passes(kb):
    """Correct LM7805 wiring must not generate critical errors."""
    components = [
        ComponentInstance(
            ref="U1",
            value="LM7805",
            lib_id="Regulator_Linear:LM7805",
            pins=[
                PinConnection("1", "IN", "+12V", "U1", "LM7805"),
                PinConnection("2", "GND", "GND", "U1", "LM7805"),
                PinConnection("3", "OUT", "+5V", "U1", "LM7805"),
            ],
        )
    ]
    report = validate_components(components, kb)
    criticals = [e for e in report.errors if e.severity == Severity.CRITICAL]
    assert not criticals, f"Correct LM7805 should have no CRITICAL errors: {[e.message_en for e in criticals]}"


# --- ATmega328P ---

def test_atmega_reset_on_gnd(kb):
    """ATmega328P RESET (pin 1) on GND must generate an error."""
    components = [
        ComponentInstance(
            ref="U1",
            value="ATmega328P",
            lib_id="MCU_Microchip_AVR:ATmega328P",
            pins=[
                PinConnection("1", "PC6/RESET", "GND", "U1", "ATmega328P"),
                PinConnection("7", "VCC", "VCC", "U1", "ATmega328P"),
                PinConnection("8", "GND", "GND", "U1", "ATmega328P"),
            ],
        )
    ]
    report = validate_components(components, kb)
    reset_errors = [e for e in report.errors if e.pin_number == "1"]
    assert reset_errors, "RESET pin on GND should generate an error"


# --- Multiple components in one schematic ---

def test_multiple_components_validated(kb):
    """Validate a schematic with both a NE555 (broken) and an LM7805 (correct)."""
    components = [
        ComponentInstance(
            ref="U1",
            value="NE555",
            lib_id="Timer:NE555",
            pins=[
                PinConnection("1", "GND", "GND", "U1", "NE555"),
                PinConnection("8", "VCC", "GND", "U1", "NE555"),  # broken
            ],
        ),
        ComponentInstance(
            ref="U2",
            value="LM7805",
            lib_id="Regulator_Linear:LM7805",
            pins=[
                PinConnection("1", "IN", "+12V", "U2", "LM7805"),
                PinConnection("2", "GND", "GND", "U2", "LM7805"),
                PinConnection("3", "OUT", "+5V", "U2", "LM7805"),
            ],
        ),
    ]
    report = validate_components(components, kb)
    assert report.checked_components == 2
    u1_errors = [e for e in report.errors if e.component_ref == "U1"]
    u2_errors = [e for e in report.errors if e.component_ref == "U2"]
    assert u1_errors, "Broken NE555 should have errors"
    assert not any(e.severity == Severity.CRITICAL for e in u2_errors), \
        "Correct LM7805 should have no critical errors"


# --- Error formatting ---

def test_error_format_english(kb):
    components = [
        ComponentInstance(
            ref="U1", value="NE555", lib_id="Timer:NE555",
            pins=[PinConnection("8", "VCC", "GND", "U1", "NE555")],
        )
    ]
    report = validate_components(components, kb)
    formatted = report.format("en")
    assert "U1" in formatted
    assert "NE555" in formatted
    assert "8" in formatted


def test_report_has_no_issues_for_correct_circuit(kb):
    components = [
        ComponentInstance(
            ref="U1", value="NE555", lib_id="Timer:NE555",
            pins=[
                PinConnection("1", "GND", "GND", "U1", "NE555"),
                PinConnection("8", "VCC", "VCC", "U1", "NE555"),
                PinConnection("4", "RST", "VCC", "U1", "NE555"),
                PinConnection("3", "OUT", "Net-OUT", "U1", "NE555"),
            ],
        )
    ]
    report = validate_components(components, kb)
    formatted = report.format("en")
    assert "No errors" in formatted

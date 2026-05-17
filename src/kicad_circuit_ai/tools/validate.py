"""Main validation engine: checks component pins against knowledge base rules."""

import logging
from pathlib import Path
from typing import Optional, Union

from kicad_circuit_ai.knowledge.loader import ComponentKnowledgeBase
from kicad_circuit_ai.knowledge.rules import is_floating, is_gnd, is_vcc, net_matches
from kicad_circuit_ai.models import (
    ComponentInstance,
    PinConnection,
    Severity,
    ValidationError,
    ValidationReport,
)

logger = logging.getLogger(__name__)

_GLOBAL_KB = None


def _get_kb() -> ComponentKnowledgeBase:
    global _GLOBAL_KB
    if _GLOBAL_KB is None:
        _GLOBAL_KB = ComponentKnowledgeBase()
    return _GLOBAL_KB


def validate_components(
    components: list[ComponentInstance],
    kb: Optional[ComponentKnowledgeBase] = None,
) -> ValidationReport:
    """Validate a list of parsed component instances against the knowledge base."""
    if kb is None:
        kb = _get_kb()

    report = ValidationReport()
    report.checked_components = len(components)

    for component in components:
        kb_entry = kb.find(component.value)
        if kb_entry is None:
            logger.debug(f"No knowledge base entry for {component.value} ({component.ref})")
            report.unknown_components.append(f"{component.ref}({component.value})")
            continue

        pin_rules: dict = kb_entry.get("pins", {})

        for pin in component.pins:
            rules = pin_rules.get(int(pin.pin_number) if pin.pin_number.isdigit() else pin.pin_number, {})
            if not rules:
                # Try string key as fallback
                rules = pin_rules.get(pin.pin_number, {})
            if not rules:
                continue

            errors = _check_pin(pin, rules, component)
            report.errors.extend(errors)

    return report


def _check_pin(
    pin: PinConnection,
    rules: dict,
    component: ComponentInstance,
) -> list[ValidationError]:
    errors = []
    net = pin.net_name
    is_critical = rules.get("critical", False)

    # Rule: must_not_be
    for forbidden_net in rules.get("must_not_be", []):
        if net_matches(net, forbidden_net):
            sev = Severity.CRITICAL if is_critical else Severity.ERROR
            errors.append(_make_error(
                sev,
                "WRONG_NET_CRITICAL" if is_critical else "WRONG_NET",
                pin, component, rules, net, forbidden_net,
            ))
            return errors  # No need to check more rules for this pin

    # Rule: must_connect_to
    required = rules.get("must_connect_to")
    if required and not net_matches(net, required) and not is_floating(net):
        sev = Severity.CRITICAL if is_critical else Severity.ERROR
        errors.append(_make_wrong_net_error(sev, pin, component, rules, net, required))

    # Rule: warn_if_floating
    if rules.get("warn_if_floating") and is_floating(net):
        optional = rules.get("optional", False)
        if not optional:
            errors.append(_make_floating_error(pin, component, rules))

    # Rule: must_connect_to when pin is floating
    if required and is_floating(net) and rules.get("critical"):
        errors.append(_make_error(
            Severity.CRITICAL, "FLOATING_CRITICAL", pin, component, rules, net, required,
        ))

    return errors


def _make_error(
    severity: Severity,
    code: str,
    pin: PinConnection,
    component: ComponentInstance,
    rules: dict,
    actual_net: str,
    expected_or_forbidden: str,
) -> ValidationError:
    pin_name = rules.get("name", pin.pin_name)
    notes = rules.get("notes", "")

    if code in ("WRONG_NET_CRITICAL", "WRONG_NET"):
        msg_en = (
            f"Pin {pin.pin_number} ({pin_name}) is connected to {actual_net}, "
            f"but must NOT be connected to {expected_or_forbidden}. {notes}"
        ).strip()
        msg_es = (
            f"Pin {pin.pin_number} ({pin_name}) está conectado a {actual_net}, "
            f"pero NO debe conectarse a {expected_or_forbidden}. {notes}"
        ).strip()
        sug_en = f"Check the schematic — is this a copy-paste error? Expected a different net."
        sug_es = f"Revisa el esquemático — ¿es un error de copiar/pegar? Se esperaba una red diferente."
    elif code == "FLOATING_CRITICAL":
        msg_en = f"Pin {pin.pin_number} ({pin_name}) is not connected. Must connect to {expected_or_forbidden}. {notes}".strip()
        msg_es = f"Pin {pin.pin_number} ({pin_name}) no está conectado. Debe conectarse a {expected_or_forbidden}. {notes}".strip()
        sug_en = f"Connect this pin to {expected_or_forbidden}."
        sug_es = f"Conecta este pin a {expected_or_forbidden}."
    else:
        msg_en = f"Pin {pin.pin_number} ({pin_name}): unexpected net {actual_net}. {notes}".strip()
        msg_es = f"Pin {pin.pin_number} ({pin_name}): red inesperada {actual_net}. {notes}".strip()
        sug_en = sug_es = ""

    return ValidationError(
        severity=severity,
        code=code,
        component_ref=component.ref,
        component_value=component.value,
        pin_number=pin.pin_number,
        pin_name=pin_name,
        net_name=actual_net,
        message_en=msg_en,
        message_es=msg_es,
        suggestion_en=sug_en,
        suggestion_es=sug_es,
    )


def _make_wrong_net_error(
    severity: Severity,
    pin: PinConnection,
    component: ComponentInstance,
    rules: dict,
    actual_net: str,
    required_net: str,
) -> ValidationError:
    pin_name = rules.get("name", pin.pin_name)
    notes = rules.get("notes", "")
    msg_en = f"Pin {pin.pin_number} ({pin_name}) is on net {actual_net}, expected {required_net}. {notes}".strip()
    msg_es = f"Pin {pin.pin_number} ({pin_name}) está en red {actual_net}, se esperaba {required_net}. {notes}".strip()
    return ValidationError(
        severity=severity,
        code="WRONG_REQUIRED_NET",
        component_ref=component.ref,
        component_value=component.value,
        pin_number=pin.pin_number,
        pin_name=pin_name,
        net_name=actual_net,
        message_en=msg_en,
        message_es=msg_es,
        suggestion_en=f"Connect Pin {pin.pin_number} to {required_net}.",
        suggestion_es=f"Conecta el Pin {pin.pin_number} a {required_net}.",
    )


def _make_floating_error(
    pin: PinConnection,
    component: ComponentInstance,
    rules: dict,
) -> ValidationError:
    pin_name = rules.get("name", pin.pin_name)
    recommended = rules.get("recommended", "")
    notes = rules.get("notes", "")
    msg_en = f"Pin {pin.pin_number} ({pin_name}) is floating (unconnected). {notes}".strip()
    msg_es = f"Pin {pin.pin_number} ({pin_name}) está flotante (sin conectar). {notes}".strip()
    return ValidationError(
        severity=Severity.WARNING,
        code="FLOATING_PIN",
        component_ref=component.ref,
        component_value=component.value,
        pin_number=pin.pin_number,
        pin_name=pin_name,
        net_name=pin.net_name,
        message_en=msg_en,
        message_es=msg_es,
        suggestion_en=recommended or "Connect or explicitly mark as no-connect.",
        suggestion_es=recommended or "Conecta o marca explícitamente como no-connect.",
    )


def validate_from_file(
    path: Union[str, Path],
    locale: str = "en",
    kb: Optional[ComponentKnowledgeBase] = None,
) -> ValidationReport:
    """Parse a schematic or netlist file and validate it. Returns ValidationReport."""
    from kicad_circuit_ai.parser import parse
    components = parse(path)
    return validate_components(components, kb)


def validate_from_netlist_path(
    path: Union[str, Path],
    component_override: Optional[str] = None,
    kb: Optional[ComponentKnowledgeBase] = None,
) -> list[ValidationError]:
    """Convenience function for tests: parse XML netlist and return error list."""
    from kicad_circuit_ai.parser.netlist import parse_netlist
    components = parse_netlist(Path(path))
    if component_override:
        for c in components:
            c.value = component_override
    report = validate_components(components, kb)
    return report.errors

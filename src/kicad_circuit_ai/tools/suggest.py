"""Generate fix suggestions for validation errors."""

from kicad_circuit_ai.knowledge.loader import ComponentKnowledgeBase
from kicad_circuit_ai.models import ValidationError


def suggest_fix(
    component_value: str,
    pin_number: str,
    current_net: str,
    locale: str = "en",
    kb: ComponentKnowledgeBase | None = None,
) -> str:
    """Return a human-readable fix suggestion for a mis-wired pin."""
    if kb is None:
        from kicad_circuit_ai.tools.validate import _get_kb
        kb = _get_kb()

    entry = kb.find(component_value)
    if not entry:
        if locale == "es":
            return f"Componente '{component_value}' no está en la base de conocimiento. Revisa el datasheet."
        return f"Component '{component_value}' not in knowledge base. Check the datasheet."

    pin_key = int(pin_number) if pin_number.isdigit() else pin_number
    rules = entry.get("pins", {}).get(pin_key, {})
    if not rules:
        rules = entry.get("pins", {}).get(pin_number, {})

    if not rules:
        if locale == "es":
            return f"No hay reglas para el pin {pin_number} de {component_value}."
        return f"No rules found for pin {pin_number} of {component_value}."

    pin_name = rules.get("name", f"Pin {pin_number}")
    must_connect = rules.get("must_connect_to", "")
    must_not = rules.get("must_not_be", [])
    notes = rules.get("notes", "")
    recommended = rules.get("recommended", "")

    lines = []
    if locale == "es":
        lines.append(f"Pin {pin_number} ({pin_name}) del {component_value}:")
        if must_not and current_net.upper() in [n.upper() for n in must_not]:
            lines.append(f"  • Actualmente en {current_net} — ¡esto es incorrecto!")
        if must_connect:
            lines.append(f"  • Debe conectarse a: {must_connect}")
        if must_not:
            lines.append(f"  • NO debe conectarse a: {', '.join(must_not)}")
        if recommended:
            lines.append(f"  • Conexión recomendada: {recommended}")
        if notes:
            lines.append(f"  • Nota: {notes}")
    else:
        lines.append(f"Pin {pin_number} ({pin_name}) of {component_value}:")
        if must_not and current_net.upper() in [n.upper() for n in must_not]:
            lines.append(f"  • Currently on {current_net} — this is incorrect!")
        if must_connect:
            lines.append(f"  • Must connect to: {must_connect}")
        if must_not:
            lines.append(f"  • Must NOT connect to: {', '.join(must_not)}")
        if recommended:
            lines.append(f"  • Recommended connection: {recommended}")
        if notes:
            lines.append(f"  • Note: {notes}")

    return "\n".join(lines)

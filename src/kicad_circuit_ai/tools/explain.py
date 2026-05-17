"""Return detailed, educational explanations for validation error codes."""

from kicad_circuit_ai.models import ValidationError


_EXPLANATIONS: dict[str, dict[str, str]] = {
    "WRONG_NET_CRITICAL": {
        "en": (
            "A critical pin is connected to the wrong net. Critical pins are those that "
            "directly affect the IC's power supply or fundamental operation. Connecting "
            "VCC to GND, for example, will short-circuit the power supply and may damage "
            "both the IC and surrounding components."
        ),
        "es": (
            "Un pin crítico está conectado a la red incorrecta. Los pines críticos son "
            "aquellos que afectan directamente la alimentación del CI o su operación fundamental. "
            "Conectar VCC a GND, por ejemplo, cortocircuitará la fuente de alimentación y puede "
            "dañar el CI y los componentes cercanos."
        ),
    },
    "WRONG_NET": {
        "en": (
            "A pin is connected to a net that is not valid for its function. "
            "This may cause unexpected behavior or prevent the circuit from working."
        ),
        "es": (
            "Un pin está conectado a una red que no es válida para su función. "
            "Esto puede causar comportamiento inesperado o impedir que el circuito funcione."
        ),
    },
    "WRONG_REQUIRED_NET": {
        "en": (
            "A pin that must be connected to a specific net (like VCC or GND) is connected "
            "to a different net. Check whether you accidentally selected the wrong wire or label."
        ),
        "es": (
            "Un pin que debe conectarse a una red específica (como VCC o GND) está conectado "
            "a otra red. Verifica si accidentalmente seleccionaste el cable o la etiqueta incorrectos."
        ),
    },
    "FLOATING_CRITICAL": {
        "en": (
            "A critical pin has no connection. For power supply pins, this means the IC has "
            "no power and will not function. For reset pins, a floating reset may cause random "
            "resets due to noise."
        ),
        "es": (
            "Un pin crítico no tiene conexión. Para pines de alimentación, esto significa que "
            "el CI no tiene energía y no funcionará. Para pines de reset, un reset flotante puede "
            "causar reinicios aleatorios debido al ruido."
        ),
    },
    "FLOATING_PIN": {
        "en": (
            "A pin is unconnected. While this may be intentional for unused pins, some pins "
            "(like RESET, ENABLE, or CHIP_SELECT) should be explicitly tied to VCC or GND "
            "rather than left floating. Floating control inputs are susceptible to noise."
        ),
        "es": (
            "Un pin no está conectado. Aunque esto puede ser intencional para pines no utilizados, "
            "algunos pines (como RESET, ENABLE o CHIP_SELECT) deben estar explícitamente conectados "
            "a VCC o GND en lugar de dejarse flotantes. Las entradas de control flotantes son "
            "susceptibles al ruido."
        ),
    },
}


def explain_error(error: ValidationError, locale: str = "en") -> str:
    """Return a detailed explanation for a validation error."""
    explanation = _EXPLANATIONS.get(error.code, {})
    if not explanation:
        return error.format(locale)

    text = explanation.get(locale, explanation.get("en", ""))
    header = error.format(locale)
    return f"{header}\n\n   Explanation: {text}" if locale == "en" else f"{header}\n\n   Explicación: {text}"


def explain_error_code(code: str, locale: str = "en") -> str:
    """Return explanation text for a given error code."""
    explanation = _EXPLANATIONS.get(code, {})
    return explanation.get(locale, explanation.get("en", f"Unknown error code: {code}"))

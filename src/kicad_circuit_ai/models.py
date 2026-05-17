"""Core data models for circuit validation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class PinConnection:
    pin_number: str
    pin_name: str
    net_name: str
    component_ref: str
    component_value: str


@dataclass
class ComponentInstance:
    ref: str
    value: str
    lib_id: str
    pins: list[PinConnection] = field(default_factory=list)


@dataclass
class ValidationError:
    severity: Severity
    code: str
    component_ref: str
    component_value: str
    pin_number: str
    pin_name: str
    net_name: str
    message_en: str
    message_es: str
    suggestion_en: str = ""
    suggestion_es: str = ""

    def format(self, locale: str = "en") -> str:
        msg = self.message_en if locale == "en" else self.message_es
        sug = self.suggestion_en if locale == "en" else self.suggestion_es
        sev_val = self.severity.value
        icon = {"CRITICAL": "❌", "ERROR": "🔴", "WARNING": "⚠️", "INFO": "ℹ️"}[sev_val]
        lines = [f"{icon} {sev_val} [{self.component_ref} {self.component_value}] Pin {self.pin_number} ({self.pin_name}): {msg}"]
        if sug:
            prefix = "→" if locale == "en" else "→"
            lines.append(f"   {prefix} {sug}")
        return "\n".join(lines)


@dataclass
class ValidationReport:
    errors: list[ValidationError] = field(default_factory=list)
    checked_components: int = 0
    unknown_components: list[str] = field(default_factory=list)

    def format(self, locale: str = "en") -> str:
        if not self.errors:
            ok = "✅ No errors found." if locale == "en" else "✅ No se encontraron errores."
            summary = f"Checked {self.checked_components} component(s)." if locale == "en" else f"Se revisaron {self.checked_components} componente(s)."
            return f"{ok}\n{summary}"

        lines = []
        criticals = [e for e in self.errors if e.severity == Severity.CRITICAL]
        errors = [e for e in self.errors if e.severity == Severity.ERROR]
        warnings = [e for e in self.errors if e.severity == Severity.WARNING]

        header = f"Found {len(self.errors)} issue(s) in {self.checked_components} component(s):" if locale == "en" else f"Se encontraron {len(self.errors)} problema(s) en {self.checked_components} componente(s):"
        lines.append(header)
        lines.append("")

        for group in [criticals, errors, warnings]:
            for err in group:
                lines.append(err.format(locale))
                lines.append("")

        if self.unknown_components:
            note = f"Note: {len(self.unknown_components)} component(s) not in knowledge base: {', '.join(self.unknown_components)}" if locale == "en" else f"Nota: {len(self.unknown_components)} componente(s) no están en la base de conocimiento: {', '.join(self.unknown_components)}"
            lines.append(note)

        return "\n".join(lines).rstrip()

"""Generate Bill of Materials from a circuit recipe JSON string."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

_LCSC_BY_SYMBOL_VALUE: dict[tuple[str, str], str] = {
    ("Timer:NE555", "ne555"): "C46749",
    ("Device:R", "10k"): "C25804",
    ("Device:R", "47k"): "C25819",
    ("Device:R", "1k"): "C17513",
    ("Device:C", "100nf"): "C14663",
    ("Device:C", "10nf"): "C1644",
    ("Device:C", "10uf"): "C19702",
    ("Device:C", "100uf"): "C49678",
    ("Regulator_Linear:LM7805", "lm7805"): "C55509",
    ("Diode:1N4001", "1n4001"): "C14526",
}


def _normalize_value(value: str) -> str:
    return value.replace("µ", "u").strip().lower()


def _lcsc_part(symbol: str, value: str) -> str:
    key = (symbol.strip(), _normalize_value(value))
    if key in _LCSC_BY_SYMBOL_VALUE:
        return _LCSC_BY_SYMBOL_VALUE[key]

    sym_l = symbol.lower()
    val_n = _normalize_value(value)
    if "ne555" in val_n or "ne555" in sym_l:
        return "C46749"
    if "lm7805" in val_n or "lm7805" in sym_l:
        return "C55509"
    if "1n4001" in val_n or "1n4001" in sym_l:
        return "C14526"
    if sym_l.startswith("device:r") and val_n == "10k":
        return "C25804"
    if sym_l.startswith("device:r") and val_n == "47k":
        return "C25819"
    if sym_l.startswith("device:r") and val_n == "1k":
        return "C17513"
    if sym_l.startswith("device:c"):
        if val_n == "100nf":
            return "C14663"
        if val_n == "10nf":
            return "C1644"
        if val_n == "10uf":
            return "C19702"
        if val_n == "100uf":
            return "C49678"
    return ""


def _ref_sort_key(ref: str) -> tuple[str, int | str]:
    m = re.match(r"^([A-Z]+)(\d+)$", ref, re.I)
    if m:
        return (m.group(1).upper(), int(m.group(2)))
    return (ref, 0)


def _aggregate_components(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[str]] = {}
    descriptions: dict[tuple[str, str, str], str] = {}

    for c in components:
        ref = str(c.get("ref", "")).strip()
        symbol = str(c.get("symbol", "")).strip()
        footprint = str(c.get("footprint", "")).strip()
        value = str(c.get("value", "")).strip()
        desc = str(c.get("description", "")).strip()
        key = (symbol, value, footprint)
        groups.setdefault(key, []).append(ref)
        if desc and key not in descriptions:
            descriptions[key] = desc

    rows: list[dict[str, Any]] = []
    for key, refs in groups.items():
        symbol, value, footprint = key
        refs_sorted = sorted(set(refs), key=_ref_sort_key)
        lcsc = _lcsc_part(symbol, value)
        rows.append({
            "Ref": ",".join(refs_sorted),
            "Value": value,
            "Footprint": footprint,
            "Qty": len(refs_sorted),
            "LCSC_Part": lcsc,
            "Description": descriptions.get(key, ""),
        })

    rows.sort(key=lambda r: _ref_sort_key(r["Ref"].split(",")[0]))
    return rows


def generate_bom_from_recipe(recipe_json: str, output_format: str = "csv") -> str:
    """Generate a Bill of Materials from a circuit recipe JSON.

    Args:
        recipe_json: JSON string from get_pcb_workflow_recipe() or parse_circuit_from_description()
        output_format: ``csv`` (default), ``json``, or ``markdown``

    Returns:
        BOM in the requested format, or an error message string.
    """
    fmt = output_format.strip().lower()
    if fmt not in {"csv", "json", "markdown"}:
        return f"Error: output_format must be csv, json, or markdown (got {output_format!r})"

    try:
        data = json.loads(recipe_json)
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON — {e}"

    if not isinstance(data, dict):
        return "Error: recipe JSON must be an object with a 'components' array"

    raw_components = data.get("components")
    if not isinstance(raw_components, list):
        return "Error: recipe must contain a 'components' list"

    rows = _aggregate_components(raw_components)

    if fmt == "json":
        return json.dumps(rows, indent=2, ensure_ascii=False)

    if fmt == "markdown":
        headers = ["Ref", "Value", "Footprint", "Qty", "LCSC_Part", "Description"]
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        ]
        for r in rows:
            cells = [
                str(r["Ref"]).replace("|", "\\|"),
                str(r["Value"]).replace("|", "\\|"),
                str(r["Footprint"]).replace("|", "\\|"),
                str(r["Qty"]),
                str(r["LCSC_Part"]).replace("|", "\\|"),
                str(r["Description"]).replace("|", "\\|"),
            ]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["Ref", "Value", "Footprint", "Qty", "LCSC_Part", "Description"],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()

"""Ordered PCB release checklist for dual MCP (kicad-circuit-ai + KiCAD-MCP-Server)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_release_plan(
    schematic_path: str | None,
    board_path: str | None,
    locale: str = "en",
) -> dict[str, Any]:
    """Build an ordered list of tool steps for pre-fabrication validation.

    Args:
        schematic_path: Path to .kicad_sch or KiCad XML .net (optional).
        board_path: Path to .kicad_pcb (optional but required for DFM).
        locale: Reserved for future localized notes.

    Returns:
        Dict with ``version``, ``steps`` (ordered), and ``notes``.
    """
    sch = schematic_path.strip() if schematic_path else None
    brd = board_path.strip() if board_path else None
    sch_path = Path(sch) if sch else None
    erc_path = sch if sch and sch.endswith(".kicad_sch") else None

    steps: list[dict[str, Any]] = []

    steps.append({
        "order": 1,
        "server": "kicad-circuit-ai",
        "tool": "validate_circuit_logic",
        "args": {
            "schematic_path": sch,
            "locale": locale,
        },
        "blocking": bool(sch and sch_path and sch_path.exists()),
        "description": "Semantic validation on .kicad_sch or KiCad XML .net.",
        **({} if sch else {"note": "Pass schematic_path to enable."}),
    })

    steps.append({
        "order": 2,
        "server": "KiCAD-MCP-Server",
        "tool": "run_erc",
        "args": {"schematicPath": erc_path},
        "blocking": bool(erc_path),
        "description": "KiCad ERC (kicad-cli). Requires .kicad_sch, not .net.",
        **({} if erc_path else {"note": "Open/save .kicad_sch and pass schematicPath for ERC."}),
    })

    steps.append({
        "order": 3,
        "server": "KiCAD-MCP-Server",
        "tool": "run_drc",
        "args": {},
        "blocking": True,
        "description": "DRC on loaded PCB. Ensure open_project + saved .kicad_pcb before run_drc.",
    })

    brd_resolved = str(Path(brd).resolve()) if brd else None
    steps.append({
        "order": 4,
        "server": "KiCAD-MCP-Server",
        "tool": "run_dfm_basic",
        "args": {"boardPath": brd_resolved},
        "blocking": bool(brd and Path(brd).exists()),
        "description": "Headless DFM on .kicad_pcb (courtyard overlap, etc.).",
        **({} if brd else {"note": "Pass board_path to absolute .kicad_pcb."}),
    })

    steps.append({
        "order": 5,
        "server": "kicad-circuit-ai",
        "tool": "generate_bom_from_recipe",
        "args": {
            "recipe_json": "<from get_pcb_workflow_recipe or parse_circuit_from_description>",
            "output_format": "csv",
        },
        "blocking": False,
        "optional": True,
        "description": "BOM from recipe when available; else export_bom on KiCAD-MCP.",
    })

    steps.append({
        "order": 6,
        "server": "KiCAD-MCP-Server",
        "tool": "export_gerber",
        "args": {"outputDir": "<set>"},
        "blocking": False,
        "description": "Gerbers only after blocking steps pass or user waived.",
    })

    notes = [
        "docs/RELEASE_PLAYBOOK.md — human-readable gate rules.",
        "Run each tool on the server named in ``server``.",
    ]

    return {
        "version": 1,
        "locale": locale,
        "schematic_path": sch,
        "board_path": brd,
        "steps": steps,
        "notes": notes,
    }


def release_plan_json(
    schematic_path: str | None = None,
    board_path: str | None = None,
    locale: str = "en",
) -> str:
    """JSON string for MCP tool response."""
    plan = build_release_plan(schematic_path, board_path, locale=locale)
    return json.dumps(plan, indent=2, ensure_ascii=False)

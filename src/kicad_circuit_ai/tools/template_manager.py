"""Pre-built KiCad project template management.

Templates are complete KiCad projects (.kicad_pro + .kicad_sch + .kicad_pcb)
with components placed and nets connected — ready to route, not yet routed.

Workflow:
  First run  → slow path (build from scratch) → save_project_as_template()
  Later runs → copy_template_project() → open_project() → autoroute()
"""

import json
import shutil
from pathlib import Path
from typing import Optional

_TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates"

_KICAD_EXTENSIONS = {".kicad_pro", ".kicad_sch", ".kicad_pcb"}


def list_available_templates() -> str:
    """List available pre-built KiCad project templates.

    Returns:
        JSON string with {"templates": [...]} or {"templates": []} if none exist.
    """
    if not _TEMPLATES_DIR.exists():
        return json.dumps({"templates": []})
    templates = [
        d.name for d in sorted(_TEMPLATES_DIR.iterdir())
        if d.is_dir() and any(d.glob("*.kicad_pro"))
    ]
    return json.dumps({"templates": templates})


def copy_template_project(circuit_type: str, dest_dir: str) -> str:
    """Copy a pre-built KiCad project template to a working directory.

    Args:
        circuit_type: Template name (e.g., "555_astable").
                      Call list_available_templates() to see options.
        dest_dir: Directory where the project copy will be created.
                  A subdirectory named circuit_type is created inside it.

    Returns:
        JSON with project_path, schematic_path, board_path — ready for open_project().
        Or JSON with error and available list if template not found.
    """
    src = _TEMPLATES_DIR / circuit_type
    if not src.exists() or not src.is_dir():
        available = json.loads(list_available_templates())["templates"]
        return json.dumps({
            "error": f"No template found for '{circuit_type}'",
            "available": available,
            "tip": "Run the slow path once, then call save_project_as_template() to create it.",
        })

    dest = Path(dest_dir) / circuit_type
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)

    # Locate the project files by extension
    pro_files = list(dest.glob("*.kicad_pro"))
    sch_files = list(dest.glob("*.kicad_sch"))
    pcb_files = list(dest.glob("*.kicad_pcb"))

    return json.dumps({
        "status": "copied",
        "project_path": str(pro_files[0].resolve()) if pro_files else None,
        "schematic_path": str(sch_files[0].resolve()) if sch_files else None,
        "board_path": str(pcb_files[0].resolve()) if pcb_files else None,
        "template_dir": str(dest.resolve()),
    }, indent=2)


def save_project_as_template(project_path: str, circuit_type: str) -> str:
    """Save a completed KiCad project as a reusable template.

    Call this ONCE after the first successful full workflow (slow path).
    Subsequent runs can use copy_template_project() to skip schematic building
    and component placement — going straight to autoroute().

    Args:
        project_path: Path to the .kicad_pro file of the completed project.
        circuit_type: Template name (e.g., "555_astable").

    Returns:
        JSON with status and template_dir path.
    """
    pro = Path(project_path)
    if not pro.exists():
        return json.dumps({"error": f"Project file not found: {project_path}"})
    if pro.suffix != ".kicad_pro":
        return json.dumps({"error": f"Expected .kicad_pro file, got: {pro.suffix}"})

    stem = pro.stem
    project_dir = pro.parent

    # Collect all KiCad project files with the same stem
    files_to_copy: list[Path] = []
    for ext in _KICAD_EXTENSIONS:
        candidate = project_dir / f"{stem}{ext}"
        if candidate.exists():
            files_to_copy.append(candidate)

    if len(files_to_copy) < 2:
        return json.dumps({
            "error": f"Need at least .kicad_pro + .kicad_sch, found only: {[f.name for f in files_to_copy]}",
            "hint": "Run sync_schematic_to_board first so the .kicad_pcb exists.",
        })

    template_dir = _TEMPLATES_DIR / circuit_type
    template_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for f in files_to_copy:
        dest = template_dir / f.name
        shutil.copy2(f, dest)
        copied.append(f.name)

    return json.dumps({
        "status": "saved",
        "circuit_type": circuit_type,
        "template_dir": str(template_dir.resolve()),
        "files_saved": copied,
    }, indent=2)

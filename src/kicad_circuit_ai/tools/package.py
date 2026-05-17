"""Packaging utilities: zip Gerber files, restrict DSN to single layer, create reports."""

import re
import zipfile
from pathlib import Path
from typing import Optional

_GERBER_EXTENSIONS = {".gbr", ".gbl", ".gtl", ".gbs", ".gts", ".gbo", ".gto",
                      ".gm1", ".drl", ".cnc", ".gbrjob", ".exc", ".xln"}


def zip_gerbers(
    folder_path: str,
    output_zip: Optional[str] = None,
) -> str:
    """Compress all Gerber and drill files in a folder into a ZIP archive.

    Args:
        folder_path: Directory containing .gbr, .drl and related files.
        output_zip: Output ZIP path. Defaults to folder_path + '.zip'.

    Returns:
        Absolute path of the created ZIP file.
    """
    src = Path(folder_path)
    if not src.exists():
        raise FileNotFoundError(f"Folder not found: {src}")

    dest = Path(output_zip) if output_zip else src.parent / f"{src.name}_gerbers.zip"

    gerber_files = [
        f for f in src.iterdir()
        if f.is_file() and f.suffix.lower() in _GERBER_EXTENSIONS
    ]

    if not gerber_files:
        # Include ALL files if no Gerber-specific ones found (fallback)
        gerber_files = [f for f in src.iterdir() if f.is_file()]

    if not gerber_files:
        raise ValueError(f"No files found in {src}")

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(gerber_files):
            zf.write(f, arcname=f.name)

    return str(dest.resolve())


def restrict_dsn_to_single_layer(
    dsn_path: str,
    layer: str = "F.Cu",
    output_path: Optional[str] = None,
) -> str:
    """Modify a Specctra DSN file to only route on a single copper layer.

    Removes all copper layer entries except the specified layer from the DSN
    structure section. Freerouting will then route on one side only.

    Args:
        dsn_path: Path to the .dsn file exported by KiCad.
        layer: Layer to keep (default "F.Cu").
        output_path: Where to write the modified DSN. Defaults to overwriting dsn_path.

    Returns:
        Path of the modified DSN file.
    """
    src = Path(dsn_path)
    if not src.exists():
        raise FileNotFoundError(f"DSN file not found: {src}")

    content = src.read_text(encoding="utf-8")

    # DSN copper layers appear as: (layer "B.Cu" (type signal) ...)
    # Strategy: comment-out / remove all copper layer blocks that are NOT the target layer.
    # KiCad DSN format: (layer "NAME" (type signal) (direction TYPE))
    copper_layer_pattern = re.compile(
        r'\(layer\s+"([^"]+)"\s+\(type\s+signal\)[^)]*\)',
        re.DOTALL,
    )

    def replace_layer(m: re.Match) -> str:
        layer_name = m.group(1)
        if layer_name == layer:
            return m.group(0)  # keep
        # Replace non-target copper layers with a comment marker
        return f'; removed layer {layer_name}'

    modified = copper_layer_pattern.sub(replace_layer, content)

    dest = Path(output_path) if output_path else src
    dest.write_text(modified, encoding="utf-8")
    return str(dest.resolve())


def create_variants_report(
    project_name: str,
    variant_results: list[dict],
    output_path: str,
) -> str:
    """Write a Markdown summary of the three PCB variants.

    Args:
        project_name: Name of the project (e.g. "555_astable").
        variant_results: List of dicts with keys: name, gerbers_zip, image_path, notes.
        output_path: Where to write the .md report.

    Returns:
        Path of the written report.
    """
    lines = [
        f"# PCB Variants Report — {project_name}",
        "",
        f"Generated {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    for i, v in enumerate(variant_results, 1):
        lines += [
            f"## Variante {i}: {v.get('name', f'Variante {i}')}",
            "",
            f"- **Gerbers ZIP:** `{v.get('gerbers_zip', 'N/A')}`",
            f"- **Imagen:** `{v.get('image_path', 'N/A')}`",
        ]
        if v.get("notes"):
            lines.append(f"- **Notas:** {v['notes']}")
        lines.append("")

    report = "\n".join(lines)
    Path(output_path).write_text(report, encoding="utf-8")
    return str(Path(output_path).resolve())

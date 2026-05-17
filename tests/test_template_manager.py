"""Tests for template_manager.py (copy_template_project, save_project_as_template)."""

import json
from pathlib import Path

import pytest

import kicad_circuit_ai.tools.template_manager as tm
from kicad_circuit_ai.tools.template_manager import (
    copy_template_project,
    save_project_as_template,
    list_available_templates,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_project(base: Path, name: str = "test_circuit") -> Path:
    """Create minimal fake KiCad project files and return path to .kicad_pro."""
    proj_dir = base / name
    proj_dir.mkdir(parents=True, exist_ok=True)
    pro = proj_dir / f"{name}.kicad_pro"
    pro.write_text('(kicad_pro (version 1))\n')
    (proj_dir / f"{name}.kicad_sch").write_text('(kicad_sch (version 20250114))\n')
    (proj_dir / f"{name}.kicad_pcb").write_text('(kicad_pcb (version 20250114))\n')
    return pro


# ── list_available_templates ──────────────────────────────────────────────────

def test_list_templates_returns_json(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", tmp_path)
    result = list_available_templates()
    data = json.loads(result)
    assert "templates" in data
    assert isinstance(data["templates"], list)


def test_list_templates_empty_when_no_templates(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", tmp_path)
    data = json.loads(list_available_templates())
    assert data["templates"] == []


def test_list_templates_missing_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", tmp_path / "nonexistent")
    data = json.loads(list_available_templates())
    assert data["templates"] == []


def test_list_templates_shows_saved_templates(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", tmp_path)
    # Create two fake template dirs
    for name in ("555_astable", "555_monostable"):
        d = tmp_path / name
        d.mkdir()
        (d / f"{name}.kicad_pro").write_text("")
    data = json.loads(list_available_templates())
    assert "555_astable" in data["templates"]
    assert "555_monostable" in data["templates"]


# ── save_project_as_template ──────────────────────────────────────────────────

def test_save_template_creates_template_dir(tmp_path, monkeypatch):
    templates_dir = tmp_path / "templates"
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", templates_dir)
    pro = _make_project(tmp_path / "projects")
    result = json.loads(save_project_as_template(str(pro), "555_astable"))
    assert result["status"] == "saved"
    assert (templates_dir / "555_astable").is_dir()


def test_save_template_copies_all_three_files(tmp_path, monkeypatch):
    templates_dir = tmp_path / "templates"
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", templates_dir)
    pro = _make_project(tmp_path / "projects")
    save_project_as_template(str(pro), "555_astable")
    template = templates_dir / "555_astable"
    assert (template / "test_circuit.kicad_pro").exists()
    assert (template / "test_circuit.kicad_sch").exists()
    assert (template / "test_circuit.kicad_pcb").exists()


def test_save_template_returns_files_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", tmp_path / "tmpl")
    pro = _make_project(tmp_path / "proj")
    result = json.loads(save_project_as_template(str(pro), "my_circuit"))
    assert len(result["files_saved"]) == 3


def test_save_template_file_not_found():
    result = json.loads(save_project_as_template("/nonexistent/proj.kicad_pro", "x"))
    assert "error" in result


def test_save_template_wrong_extension(tmp_path):
    wrong = tmp_path / "proj.kicad_sch"
    wrong.write_text("")
    result = json.loads(save_project_as_template(str(wrong), "x"))
    assert "error" in result


def test_save_template_missing_sch_returns_error(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", tmp_path / "tmpl")
    proj_dir = tmp_path / "proj"
    proj_dir.mkdir()
    pro = proj_dir / "minimal.kicad_pro"
    pro.write_text("")
    # Only .kicad_pro, no .kicad_sch
    result = json.loads(save_project_as_template(str(pro), "x"))
    assert "error" in result


def test_save_template_overwrites_existing(tmp_path, monkeypatch):
    templates_dir = tmp_path / "tmpl"
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", templates_dir)
    pro = _make_project(tmp_path / "proj")
    save_project_as_template(str(pro), "555_astable")
    # Modify original and save again
    pro.write_text("(kicad_pro (version 2))\n")
    save_project_as_template(str(pro), "555_astable")
    content = (templates_dir / "555_astable" / "test_circuit.kicad_pro").read_text()
    assert "version 2" in content


# ── copy_template_project ─────────────────────────────────────────────────────

def test_copy_template_not_found_returns_error(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", tmp_path)
    result = json.loads(copy_template_project("nonexistent", str(tmp_path / "dest")))
    assert "error" in result
    assert "available" in result


def test_copy_template_roundtrip(tmp_path, monkeypatch):
    templates_dir = tmp_path / "tmpl"
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", templates_dir)
    pro = _make_project(tmp_path / "proj")
    save_project_as_template(str(pro), "555_astable")

    dest_dir = tmp_path / "working"
    result = json.loads(copy_template_project("555_astable", str(dest_dir)))
    assert result["status"] == "copied"
    assert Path(result["project_path"]).exists()
    assert Path(result["schematic_path"]).exists()
    assert Path(result["board_path"]).exists()


def test_copy_template_returns_absolute_paths(tmp_path, monkeypatch):
    templates_dir = tmp_path / "tmpl"
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", templates_dir)
    pro = _make_project(tmp_path / "proj")
    save_project_as_template(str(pro), "555_astable")
    result = json.loads(copy_template_project("555_astable", str(tmp_path / "work")))
    assert Path(result["project_path"]).is_absolute()
    assert Path(result["board_path"]).is_absolute()


def test_copy_template_preserves_file_contents(tmp_path, monkeypatch):
    templates_dir = tmp_path / "tmpl"
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", templates_dir)
    pro = _make_project(tmp_path / "proj")
    save_project_as_template(str(pro), "555_astable")

    result = json.loads(copy_template_project("555_astable", str(tmp_path / "work")))
    copied_pro = Path(result["project_path"]).read_text()
    assert "(kicad_pro" in copied_pro


def test_copy_template_idempotent_overwrites_dest(tmp_path, monkeypatch):
    templates_dir = tmp_path / "tmpl"
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", templates_dir)
    pro = _make_project(tmp_path / "proj")
    save_project_as_template(str(pro), "555_astable")

    dest = str(tmp_path / "work")
    copy_template_project("555_astable", dest)
    result = json.loads(copy_template_project("555_astable", dest))
    assert result["status"] == "copied"


def test_copy_template_error_shows_available(tmp_path, monkeypatch):
    templates_dir = tmp_path / "tmpl"
    monkeypatch.setattr(tm, "_TEMPLATES_DIR", templates_dir)
    pro = _make_project(tmp_path / "proj")
    save_project_as_template(str(pro), "555_astable")

    result = json.loads(copy_template_project("unknown_circuit", str(tmp_path / "work")))
    assert "error" in result
    assert "555_astable" in result["available"]

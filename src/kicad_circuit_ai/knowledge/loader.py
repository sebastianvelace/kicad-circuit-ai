"""Load component YAML files from the knowledge base directory."""

import logging
import os
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_COMPONENTS_DIR = Path(__file__).parent.parent.parent.parent / "components"


def _get_components_dir() -> Path:
    env_path = os.environ.get("KICAD_AI_COMPONENTS_DIR")
    if env_path:
        return Path(env_path)
    return _DEFAULT_COMPONENTS_DIR


class ComponentKnowledgeBase:
    def __init__(self, components_dir: Optional[Path] = None):
        self._dir = components_dir or _get_components_dir()
        self._cache: dict[str, dict] = {}
        self._alias_map: dict[str, str] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not self._dir.exists():
            logger.warning(f"Components directory not found: {self._dir}")
            self._loaded = True
            return
        for yaml_file in self._dir.glob("*.yaml"):
            if yaml_file.name.startswith("_"):
                continue
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data or "component" not in data:
                    continue
                comp = data["component"]
                primary_name = comp["name"].upper()
                self._cache[primary_name] = data
                for alias in comp.get("aliases", []):
                    self._alias_map[alias.upper()] = primary_name
            except Exception as e:
                logger.warning(f"Failed to load {yaml_file.name}: {e}")
        self._loaded = True

    def find(self, component_value: str) -> Optional[dict]:
        self._ensure_loaded()
        key = component_value.strip().upper()
        if key in self._cache:
            return self._cache[key]
        if key in self._alias_map:
            return self._cache.get(self._alias_map[key])
        # Partial match: e.g. "NE555P" matches "NE555"
        for name in self._cache:
            if key.startswith(name) or name.startswith(key):
                return self._cache[name]
        return None

    def list_components(self) -> list[str]:
        self._ensure_loaded()
        return sorted(self._cache.keys())

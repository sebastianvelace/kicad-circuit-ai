"""Shared test fixtures and configuration."""

import sys
from pathlib import Path

# Ensure src is on the path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

FIXTURES = Path(__file__).parent / "fixtures"
COMPONENTS = Path(__file__).parent.parent / "components"

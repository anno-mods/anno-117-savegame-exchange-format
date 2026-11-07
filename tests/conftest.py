"""Shared paths and fixtures. Every test runs offline from the files in the repository unless it says otherwise.

Environment variables (all optional):
    ANNO_PLANNER_REPO   checkout of Anno-117-Planner  -> enables planner game data and plan tests
    ANNO_DECODED        folder with the decoded Marcia 69 save (data_raw.xml, session_0..2.xml) -> enables decode tests
"""
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW_CONFIG = ROOT / "data" / "raw" / "calculator_configs" / "Marcia 69.json"
NEW_DIR = ROOT / "data" / "processed" / "calculator_configs"
NEW_CONFIG = NEW_DIR / "Marcia 69 updated.json"
NEW_REPORT = NEW_DIR / "Marcia 69 updated.changes.json"
NEW_CSV = NEW_DIR / "Marcia 69 updated.changes.csv"
PLAN_DIR = ROOT / "data" / "processed" / "planner_plans"
RESULTS = ROOT / "docs" / "analysis" / "derived-trade-flow-accuracy" / "results"


def planner_repo():
    value = os.environ.get("ANNO_PLANNER_REPO")
    if value and (Path(value) / "paxplanner").is_dir():
        return Path(value)
    return None


@pytest.fixture(scope="session")
def old_config():
    return json.loads(RAW_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def new_config():
    return json.loads(NEW_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def planner_path():
    """Planner checkout put on sys.path; skips the test when ANNO_PLANNER_REPO is not set."""
    import sys

    repo = planner_repo()
    if repo is None:
        pytest.skip("ANNO_PLANNER_REPO not set (or no paxplanner package in it)")
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    return repo

"""Shared paths and helpers of the calculator-config pipeline.

Locations come from environment variables; every default is relative to this repository
(ROOT = two folders above scripts/calculator_config):

    ANNO_DECODED        decoded save (data_raw.xml, session_0..2.xml)   default ROOT/outputs/decoded
    ANNO_CALC_REPO      checkout of anno-117-calculator                 default ROOT/../anno-117-calculator
    ANNO_PLANNER_REPO   checkout of Anno-117-Planner                    default ROOT/../Anno-117-Planner
    ANNO_LAYOUT_REPO    checkout of Anno-117-Layout-Tool                default ROOT/../Anno-117-Layout-Tool
    ANNO_OUT            working/output folder of the pipeline           default ROOT/outputs
"""
import json
import os
import pickle
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def _env_path(name, default):
    return Path(os.environ.get(name) or default)


DECODED = _env_path("ANNO_DECODED", ROOT / "outputs" / "decoded")
CALC_REPO = _env_path("ANNO_CALC_REPO", ROOT.parent / "anno-117-calculator")
PLANNER_REPO = _env_path("ANNO_PLANNER_REPO", ROOT.parent / "Anno-117-Planner")
LAYOUT_REPO = _env_path("ANNO_LAYOUT_REPO", ROOT.parent / "Anno-117-Layout-Tool")
OUT = _env_path("ANNO_OUT", ROOT / "outputs")

# Inputs that ship with the repository
#
# Inputs and output name of another save: ANNO_OLD_CONFIG (calculator config dump), ANNO_PLAN (plan written by
# savegame_to_planner.py), ANNO_FX_REPORT (its --report file), ANNO_TRADE_VISITS (visits.json of extract_trade.py),
# ANNO_OUT_STEM (output file stem, default "Marcia 69 updated").
OLD = _env_path("ANNO_OLD_CONFIG", DATA / "raw" / "calculator_configs" / "Marcia 69.json")
PLAN = _env_path("ANNO_PLAN", DATA / "processed" / "planner_plans" / "marcia69.v5.plan.json")
FX_REPORT = _env_path("ANNO_FX_REPORT", DATA / "processed" / "reports" / "fx_report_v5.json")
TRADE_VISITS = _env_path("ANNO_TRADE_VISITS", DATA / "processed" / "reports" / "trade_visits.json")

# Intermediate and final files of the pipeline (in OUT)
OUT_STEM = os.environ.get("ANNO_OUT_STEM") or "Marcia 69 updated"
PARAMS = OUT / "params.json"
SAVE_PKL = OUT / "save_data.pkl"
NEW_JSON = OUT / (OUT_STEM + ".json")
NEW_REPORT = OUT / (OUT_STEM + ".changes.json")
NEW_CSV = OUT / (OUT_STEM + ".changes.csv")

REGION_CODE = {3245: 1, 6627: 3, 149679: 4}


def load():
    """Return (original config, calculator params, planner plan, save tables, planner trade report)."""
    d = json.load(open(OLD, encoding="utf-8"))
    params = json.load(open(PARAMS, encoding="utf-8"))
    plan = json.load(open(PLAN, encoding="utf-8"))
    save = pickle.load(open(SAVE_PKL, "rb"))
    rep = json.load(open(FX_REPORT, encoding="utf-8"))
    return d, params, plan, save, rep


def island_stores(d):
    """Return (island names, {name: parsed per-island store}) of a calculator config dump."""
    names = json.loads(d["islandNames"])
    return names, {n: json.loads(d[n]) for n in names}


def area_key(store):
    """Savegame area key of an island store: areaIndex << 13 | islandID << 6 | region code (None without game connector)."""
    iid = store.get("gameConnector.islandID")
    ai = store.get("gameConnector.areaIndex")
    if iid is None or ai is None:
        return None
    return (int(ai) << 13) | (int(iid) << 6) | REGION_CODE[int(store["session"])]


def add_layout_repo_to_path():
    """Make savegame_to_planner, savegame_parser and tool_manager of the layout repo importable."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(LAYOUT_REPO / "tools" / "savegame_to_planner"))
    sys.path.insert(0, str(LAYOUT_REPO))

"""Decoded Marcia 69 save: area keys, sessions and island names (slow; needs the decoded XML and the layout repo).

Environment:
    ANNO_DECODED      folder with data_raw.xml and session_0..2.xml (savegame_to_planner.py --work-dir, or scripts/probes/savegame/decode.py)
    ANNO_LAYOUT_REPO  layout tool checkout providing savegame_to_planner / savegame_parser (default ../Anno-117-Layout-Tool)
    ANNO_TEXTS        optional texts_english.xml; enables the island-name test
RdaConsole and FileDBReader are only needed to produce the decoded folder; this test decodes nothing itself.
"""
import json
import os
import sys
from pathlib import Path

import pytest

from conftest import ROOT

pytestmark = [pytest.mark.slow, pytest.mark.needs_save]

SESSION_GUIDS = [3245, 6627, 149679]
REGION_CODES = {3245: 1, 6627: 3, 149679: 4}


def _decoded():
    value = os.environ.get("ANNO_DECODED")
    if not value:
        pytest.skip("ANNO_DECODED not set (decoded Marcia 69 folder)")
    folder = Path(value)
    needed = ["data_raw.xml", "session_0.xml", "session_1.xml", "session_2.xml"]
    missing = [n for n in needed if not (folder / n).is_file()]
    if missing:
        pytest.skip("ANNO_DECODED lacks %s" % missing)
    return folder


@pytest.fixture(scope="module")
def script():
    layout = Path(os.environ.get("ANNO_LAYOUT_REPO") or ROOT.parent / "Anno-117-Layout-Tool")
    tool = layout / "tools" / "savegame_to_planner"
    if not (tool / "savegame_to_planner.py").is_file():
        pytest.skip("layout repo not found at %s (set ANNO_LAYOUT_REPO)" % layout)
    sys.dont_write_bytecode = True
    for p in (str(tool), str(layout)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import savegame_to_planner

    return savegame_to_planner


@pytest.fixture(scope="module")
def decoded(script):
    folder = _decoded()
    guids = script.session_guids(folder / "data_raw.xml")
    sessions = [script.read_session(folder / ("session_%d.xml" % i)) for i in range(3)]
    return guids, sessions


def test_three_sessions_with_known_guids(decoded):
    guids, sessions = decoded
    assert guids == SESSION_GUIDS
    assert len(sessions) == 3


def test_area_key_decode_gives_22_player_islands(decoded, old_config):
    guids, sessions = decoded
    keys = set()
    for guid, areas in zip(guids, sessions):
        for area in areas:
            key = area["key"]
            assert key & 63 == REGION_CODES[guid], "region code of area %d does not match its session" % key
            assert (key >> 6) & 127 >= 1                  # island id, 1-based index into the map template
            assert (key >> 13) >= 1                       # area index
            keys.add(key)
    assert len(keys) == 22
    # the calculator config carries the same (areaIndex, islandID, session) triples
    expected = set()
    for name in json.loads(old_config["islandNames"]):
        store = json.loads(old_config[name])
        if "gameConnector.islandID" in store:
            code = REGION_CODES[int(store["session"])]
            expected.add((int(store["gameConnector.areaIndex"]) << 13) | (int(store["gameConnector.islandID"]) << 6) | code)
    assert expected == keys


def test_island_names_resolve_against_the_calculator_config(script, decoded, old_config):
    texts_path = os.environ.get("ANNO_TEXTS")
    if not texts_path or not Path(texts_path).is_file():
        pytest.skip("ANNO_TEXTS not set (texts_english.xml of the game)")
    texts = script.load_texts(Path(texts_path))
    _, sessions = decoded
    names = set(json.loads(old_config["islandNames"]))
    resolved = []
    for areas in sessions:
        for area in areas:
            resolved.append(area.get("cityName") or texts.get(area.get("cityNameGuid")))
    assert len(resolved) == 22
    assert all(n in names for n in resolved), [n for n in resolved if n not in names]

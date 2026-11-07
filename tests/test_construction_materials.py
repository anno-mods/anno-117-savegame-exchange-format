"""Construction-material example (Cinis, Latium Sawmill): old config, updated config and planner game data."""
import json

import pytest

SAWMILL = 3089            # "Production Construction Roman Timber", the Latium Sawmill
WOOD_PER_SAWMILL = 2.0    # t/min of Wood consumed by one sawmill (planner game data)


def _cinis(cfg):
    return json.loads(cfg["Cinis"])


def test_original_cinis_sawmill_has_constructed_4_and_no_fully_utilize_key(old_config):
    store = _cinis(old_config)
    assert int(store["%d.buildings.constructed" % SAWMILL]) == 4
    assert "%d.buildings.fullyUtilizeConstructed" % SAWMILL not in store


def test_updated_config_keeps_sawmill_count_and_adds_no_fully_utilize_key(new_config):
    store = _cinis(new_config)
    assert int(store["%d.buildings.constructed" % SAWMILL]) == 4
    assert "%d.buildings.fullyUtilizeConstructed" % SAWMILL not in store


def test_sawmill_needs_2_tons_wood_per_minute_in_planner_data(planner_path):
    from paxplanner.model.gamedata import GameData

    gd = GameData()
    factory = gd.factories[SAWMILL]
    wood = [i for i in factory.raw["inputs"] if gd.name(i["product"], "english") == "Wood"]
    assert len(wood) == 1
    cycle = factory.raw["cycleTime"]
    per_min = wood[0]["amount"] * 60.0 / cycle
    assert per_min == pytest.approx(WOOD_PER_SAWMILL)
    assert 4 * per_min == pytest.approx(8.0)

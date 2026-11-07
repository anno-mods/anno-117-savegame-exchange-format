"""Planner plans of data/processed/planner_plans load, round-trip and solve (needs ANNO_PLANNER_REPO)."""
import pytest

from conftest import PLAN_DIR

PLANS = {
    "marcia69.v4.plan.json": 22,
    "marcia69.v5.plan.json": 22,
    "autosave3774.plan.json": 31,
}


@pytest.fixture(scope="module")
def game_data(planner_path):
    from paxplanner.model.gamedata import GameData

    return GameData()


@pytest.fixture(scope="module", params=sorted(PLANS))
def plan(request, planner_path):
    from paxplanner.model.project import Plan

    return request.param, Plan.load(PLAN_DIR / request.param)


def test_plan_loads_with_expected_island_count(plan):
    name, loaded = plan
    assert len(loaded.islands) == PLANS[name]


def test_plan_json_round_trip_is_identical(plan):
    from paxplanner.model.project import Plan

    _, loaded = plan
    first = loaded.to_json()
    assert Plan.from_json(first).to_json() == first


def test_engine_solves_every_island(plan, game_data):
    from paxplanner.model.engine import Engine

    _, loaded = plan
    results = Engine(game_data, loaded).solve()
    assert set(results) == {i.id for i in loaded.islands}

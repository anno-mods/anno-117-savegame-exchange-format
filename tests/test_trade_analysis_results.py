"""Headline numbers of docs/analysis/derived-trade-flow-accuracy/analysis.md, recomputed from results/*.csv (offline)."""
import csv
import statistics

from conftest import RESULTS

PLAYER = "41"


def _rows(name):
    with (RESULTS / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_roles_predict_the_sign_of_the_measured_net():
    rows = {(r["role"], r["sign_of_measured_net"]): int(r["pairs"]) for r in _rows("role_vs_sign.csv")}
    # sources give the good away (negative net), sinks receive it (positive net); no exception in either role
    assert rows.get(("src", "pos"), 0) == 0 and rows.get(("snk", "neg"), 0) == 0
    consistent = rows[("src", "neg")] + rows[("snk", "pos")]
    assert consistent == 293
    # relays: 120 received (+), 13 gave (-)
    assert rows[("rel", "pos")] == 120
    assert rows[("rel", "neg")] == 13


def _mean_error(test, algorithm):
    values = [float(r["error"]) for r in _rows("split_cases.csv") if r["test"] == test and r["algorithm"] == algorithm]
    return len(values), statistics.mean(values)


def test_split_rule_a_weight_versus_equal_split():
    n_weight, weight = _mean_error("A", "weight_amount")
    n_equal, equal = _mean_error("A", "equal")
    assert n_weight == n_equal == 52
    assert round(weight, 2) == 0.23
    assert round(equal, 2) == 0.39
    assert weight < equal


def test_nine_player_slots_below_50_tons_in_five_routes():
    below = [r for r in _rows("slot_amounts.csv") if r["owner"] == PLAYER and r["amount"] not in ("", "None") and float(r["amount"]) < 50]
    assert len(below) == 9
    assert len({r["route"] for r in below}) == 5
    above = [r for r in _rows("slot_amounts.csv") if r["owner"] == PLAYER and r["amount"] not in ("", "None") and float(r["amount"]) > 50]
    assert not above


def test_constellation_counts():
    counts = {r["class"]: int(r["routes"]) for r in _rows("constellations.csv")}
    assert counts["distribution: 1 source; 2 or more receivers"] == 57
    assert counts["point to point: 1 source; 1 receiver"] == 53
    assert counts["relay: a stop loads and unloads the same good"] == 40

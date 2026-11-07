"""Checks on the updated calculator config against the original and its change report (offline)."""
import collections
import csv
import json
import re

import pytest

from conftest import NEW_CSV, NEW_REPORT

TRADE_FIELDS = {"productGUID", "from", "to", "userSetAmount", "isDefaultSupplier"}

PERSIST_PATTERNS = [
    r"^\d+\.buildings\.(constructed|planned|fullyUtilizeConstructed)$",
    r"^\d+\[\d+\]\.(checked|notes)$",
    r"^\d+\[\d+\]\.scaling$",
    r"^\d+\.aqueductBuff\.checked$",
    r"^\d+\.module\[\d+\]\.checked$",
    r"^island\.effect\.\d+\.scaling$",
    r"^island\.fertility\.\d+\.checked$",
    r"^\d+\.defaultSupplier\.(type|id)$",
    r"^session$",
    r"^selectedPatron$",
    r"^devotion$",
    r"^gameConnector\.(islandID|areaIndex)$",
    r"^passiveTrade\.userSetAmount$",
    r"^\d+\.(notes|effectCoverage)$",
]


def _stores(cfg):
    names = json.loads(cfg["islandNames"])
    return names, {n: json.loads(cfg[n]) for n in names}


def test_top_level_keys_unchanged(old_config, new_config):
    assert list(new_config) == list(old_config)


@pytest.mark.parametrize("key", ["islandNames", "versionCalculator", "calculatorSettings", "collapsibleStates"])
def test_selected_keys_unchanged(old_config, new_config, key):
    assert new_config[key] == old_config[key]


def test_island_stores_parse_as_json(new_config):
    names, stores = _stores(new_config)
    assert len(names) >= 22
    for n, store in stores.items():
        assert isinstance(store, dict), n


def test_island_store_keys_match_persist_patterns(new_config):
    _, stores = _stores(new_config)
    regexes = [re.compile(p) for p in PERSIST_PATTERNS]
    unknown = sorted({k for store in stores.values() for k in store if not any(r.match(k) for r in regexes)})
    assert not unknown, "keys without a known persist pattern: %s" % unknown[:20]


def test_original_stores_match_persist_patterns_too(old_config):
    _, stores = _stores(old_config)
    regexes = [re.compile(p) for p in PERSIST_PATTERNS]
    unknown = sorted({k for store in stores.values() for k in store if not any(r.match(k) for r in regexes)})
    assert not unknown, "keys without a known persist pattern: %s" % unknown[:20]


@pytest.fixture(scope="module")
def routes(new_config, old_config):
    return json.loads(old_config["tradeRoutes"]), json.loads(new_config["tradeRoutes"])


def test_trade_route_fields(routes):
    _, new = routes
    assert new
    bad = [r for r in new if set(r) != TRADE_FIELDS]
    assert not bad, bad[:3]


def test_original_routes_come_first_and_unchanged(routes):
    old, new = routes
    assert len(old) >= 40
    assert new[:40] == old[:40]
    assert new[: len(old)] == old
    assert len(new) > len(old)


def test_no_duplicate_product_from_to(routes):
    _, new = routes
    counts = collections.Counter((r["productGUID"], r["from"], r["to"]) for r in new)
    assert max(counts.values()) == 1, [k for k, v in counts.items() if v > 1][:5]


def test_at_most_one_default_supplier_per_island_and_product(routes):
    _, new = routes
    counts = collections.Counter((r["to"], r["productGUID"]) for r in new if r["isDefaultSupplier"])
    assert max(counts.values()) == 1, [k for k, v in counts.items() if v > 1][:5]


def test_no_cycles_in_default_supplier_chains(routes):
    _, new = routes
    default_from = {(r["to"], r["productGUID"]): r["from"] for r in new if r["isDefaultSupplier"]}
    for (island, product), supplier in default_from.items():
        seen = {island}
        cur = supplier
        while cur is not None:
            assert cur not in seen, "cycle for product %s through %s" % (product, cur)
            seen.add(cur)
            cur = default_from.get((cur, product))


def test_routes_connect_known_islands_and_no_self_route(routes, new_config):
    _, new = routes
    names = set(json.loads(new_config["islandNames"]))
    assert all(r["from"] in names and r["to"] in names and r["from"] != r["to"] for r in new)


def test_report_counts_of_the_shipped_config():
    report = json.loads(NEW_REPORT.read_text(encoding="utf-8"))
    assert report["summary"]["changes"] == 928
    assert report["summary"]["by_category"]["local producers"] == 29
    assert report["summary"]["by_category"]["tradeRoutes"] == len(report["trade"]["added"]) == 329
    assert len(report["changes"]) == 1156


def test_total_trade_entries(routes):
    old, new = routes
    assert len(old) == 40
    assert len(new) == 369


def test_local_producer_pairs_import_without_minimum(routes, new_config):
    """R51: an island that produces a good itself has the local producer fully utilized; routes carry no amount."""
    report = json.loads(NEW_REPORT.read_text(encoding="utf-8"))
    flags = report["trade"]["flags_set"]
    assert len(flags) == 33
    _, stores = _stores(new_config)
    cm_factories = {r["factory"] for r in report["construction_materials_overview"]}
    for flag in flags:
        value = stores[flag["island"]].get("%d.buildings.fullyUtilizeConstructed" % flag["factory"])
        assert value == "1" or (value is None and flag["factory"] in cm_factories), flag
    _, new = routes
    pairs = {(f["island"], f["product"]) for f in flags}
    assert len(pairs) == 33
    for r in new[40:]:
        if (r["to"], r["productGUID"]) in pairs:
            assert r["userSetAmount"] == 0, r
    for pair in pairs:
        defaults = [r for r in new if (r["to"], r["productGUID"]) == pair and r["isDefaultSupplier"]]
        assert len(defaults) == 1, pair


def test_user_default_supplier_kept_for_pairs_listed_as_differences():
    report = json.loads(NEW_REPORT.read_text(encoding="utf-8"))
    kept = {(k["island"], k["productGUID"]) for k in report["trade"]["local_kept"]}
    assert kept == {("Cinis", 31695), ("Juliana", 31700)}


def test_report_totals_match_csv():
    report = json.loads(NEW_REPORT.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(NEW_CSV.open(encoding="utf-8", newline="")))
    changed = [r for r in rows if r["source"] != "unchanged"]
    assert report["summary"]["changes"] == len(changed)
    assert sum(report["summary"]["by_category"].values()) == len(changed)
    assert sum(report["summary"]["by_island"].values()) == len(changed)
    assert report["summary"]["unchanged_rows"] == len(rows) - len(changed)
    assert len(report["changes"]) == len(rows)
    by_cat = collections.Counter(r["category"] for r in changed)
    assert dict(by_cat) == report["summary"]["by_category"]

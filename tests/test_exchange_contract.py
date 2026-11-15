"""Run the shared fixture contract through the repository's normal test command."""
import copy
import json
import runpy
from pathlib import Path


def test_exchange_fixtures():
    validator = runpy.run_path(str(Path(__file__).with_name("validate-fixtures.py")))
    assert validator["main"]() == 0


def test_island_edit_pairs_preserve_unrelated_data():
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    manifest = json.loads((fixtures / "MANIFEST.json").read_text(encoding="utf-8"))
    for entry in manifest["fixtures"]:
        pair = entry.get("pair", {})
        if pair.get("role") != "before":
            continue
        before = json.loads((fixtures / entry["file"]).read_text(encoding="utf-8"))
        after = json.loads((fixtures / pair["other"]).read_text(encoding="utf-8"))
        expected = copy.deepcopy(before)
        if pair["relation"] == "rename":
            renamed = pair["renamed"]
            name = next(i["name"] for i in after["islands"] if i["id"] == renamed)
            island = next(i for i in expected["islands"] if i["id"] == renamed)
            assert island["name"] != name
            island["name"] = name
        else:
            deleted = pair["deleted"]
            expected["islands"] = [i for i in expected["islands"] if i["id"] != deleted]
            trade = expected.get("trade", {})
            for route in trade.get("routes", []):
                route["stations"] = [s for s in route["stations"] if s.get("island") != deleted]
            for key in ("imports", "visits"):
                if key in trade:
                    trade[key] = [r for r in trade[key] if r.get("island") != deleted]
            for flow in trade.get("imports", []):
                flow["suppliers"] = [s for s in flow["suppliers"] if s.get("island") != deleted]
            if "history" in expected:
                expected["history"] = [s for s in expected["history"] if s.get("island") != deleted]
            for key in ("live", "computed"):
                expected.get(key, {}).get("islands", {}).pop(deleted, None)
        assert after == expected, entry["file"]

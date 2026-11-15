"""Validate the schema and every fixture against fixtures/MANIFEST.json.

Run (one command, no setup):

    uv run --with jsonschema python tests/validate-fixtures.py

or, with jsonschema installed:  python tests/validate-fixtures.py

Checks:
  1. The schema validates against the draft 2020-12 meta-schema.
  2. Every file under fixtures/ is listed in MANIFEST.json and vice versa.
  3. Every valid fixture passes the envelope check, the schema and the semantic checks.
  4. Every invalid fixture fails exactly in the class the manifest names:
       envelope - rejected by envelope_check() (format marker, major version, JSON shape)
       schema   - passes envelope_check(), fails the JSON Schema at the manifest's path/keyword
       semantic - passes the JSON Schema, fails semantic_check() with the manifest's code
  5. Fixture sanity: gameIsland.areaKey agrees with areaIndex and islandId.
  6. The vendoring script copies, records a VERSION and detects a differing copy.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(ROOT, "schema", "anno117-exchange.schema.json")
FIXTURES = os.path.join(ROOT, "fixtures")
MANIFEST_PATH = os.path.join(FIXTURES, "MANIFEST.json")
SUPPORTED_MAJOR = 1
FORMAT_MARKER = "anno117-exchange"
CLASSES = ("envelope", "schema", "semantic")

failures = []


def fail(msg):
    failures.append(msg)
    print("FAIL: " + msg)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def envelope_check(doc):
    """Return None when the envelope is acceptable, else a reason code."""
    if not isinstance(doc, dict):
        return "not-object"
    if doc.get("format") != FORMAT_MARKER:
        return "wrong-format"
    version = doc.get("formatVersion")
    if not isinstance(version, str):
        return "missing-formatVersion"
    parts = version.split(".")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return "malformed-formatVersion"
    if int(parts[0]) > SUPPORTED_MAJOR:
        return "unsupported-major"
    generator = doc.get("generator")
    if not isinstance(generator, dict) or not isinstance(generator.get("name"), str):
        return "missing-generator-name"
    islands = doc.get("islands")
    if not isinstance(islands, list):
        return "missing-islands"
    for isl in islands:
        if not isinstance(isl, dict) or not isinstance(isl.get("id"), str):
            return "missing-island-id"
    return None


def item_records(doc):
    """Yield every item record in every place of R56."""
    for isl in doc.get("islands", []) if isinstance(doc.get("islands"), list) else []:
        if not isinstance(isl, dict):
            continue
        for holder in isl.get("itemHolders", []) or []:
            if isinstance(holder, dict):
                for key in ("items", "carried"):
                    for rec in holder.get(key, []) or []:
                        yield rec
        for rec in isl.get("itemStorage", []) or []:
            yield rec
    account = doc.get("account")
    if isinstance(account, dict):
        for rec in account.get("items", []) or []:
            yield rec
    for rec in doc.get("unlocatedItems", []) or []:
        yield rec


def semantic_check(doc):
    """Return None, or a reason code for a rule the JSON Schema cannot express."""
    seen = set()
    for rec in item_records(doc):
        if isinstance(rec, dict) and "instance" in rec:
            if rec["instance"] in seen:
                return "duplicate-instance"
            seen.add(rec["instance"])
    ids = set()
    for isl in doc.get("islands", []):
        if isl["id"] in ids:
            return "duplicate-island-id"
        ids.add(isl["id"])
    return None


def area_key_problems(doc):
    out = []
    for isl in doc.get("islands", []):
        gi = isl.get("gameIsland") if isinstance(isl, dict) else None
        if not isinstance(gi, dict):
            continue
        key, idx, iid = gi.get("areaKey"), gi.get("areaIndex"), gi.get("islandId")
        if None in (key, idx, iid):
            continue
        if (key >> 13) != idx or ((key >> 6) & 0x7F) != iid:
            out.append("areaKey %s does not match areaIndex %s / islandId %s" % (key, idx, iid))
    return out


def main():
    failures.clear()
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("jsonschema is missing; run: uv run --with jsonschema python tests/validate-fixtures.py")
        return 2

    if not os.path.exists(SCHEMA_PATH):
        fail("schema file missing: " + os.path.relpath(SCHEMA_PATH, ROOT))
        print("\n%d failure(s)" % len(failures))
        return 1
    schema = load(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
        print("ok   schema is a valid draft 2020-12 schema")
    except Exception as exc:  # noqa: BLE001
        fail("schema fails the meta-schema: %s" % exc)
        return 1
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must declare draft 2020-12 in $schema")
    validator = Draft202012Validator(schema)

    manifest = load(MANIFEST_PATH)
    entries = manifest["fixtures"]
    listed = {e["file"] for e in entries}
    if len(listed) != len(entries):
        fail("duplicate fixture entries in MANIFEST")
    on_disk = set()
    for sub in ("valid", "invalid"):
        for name in sorted(os.listdir(os.path.join(FIXTURES, sub))):
            if name.endswith(".json"):
                on_disk.add(sub + "/" + name)
    for missing in sorted(on_disk - listed):
        fail("fixture not in MANIFEST: " + missing)
    for ghost in sorted(listed - on_disk):
        fail("MANIFEST entry without file: " + ghost)

    used_classes = set()
    for entry in entries:
        rel = entry["file"]
        if rel not in on_disk:
            continue
        before = len(failures)
        doc = load(os.path.join(FIXTURES, rel))
        errors = list(validator.iter_errors(doc))
        env = envelope_check(doc)
        sem = semantic_check(doc) if not errors and env is None else None
        if entry["valid"]:
            if not rel.startswith("valid/"):
                fail("%s: valid flag true but file is not under valid/" % rel)
            if env is not None:
                fail("%s: envelope check failed: %s" % (rel, env))
            for err in errors[:3]:
                fail("%s: schema error at /%s: %s" % (rel, "/".join(map(str, err.absolute_path)), err.message[:120]))
            if sem:
                fail("%s: semantic check failed: %s" % (rel, sem))
            for prob in area_key_problems(doc):
                fail("%s: %s" % (rel, prob))
            if not entry.get("description"):
                fail("%s: manifest entry needs a description" % rel)
            if len(failures) == before:
                print("ok   " + rel)
            continue
        cls = entry.get("class")
        used_classes.add(cls)
        if not rel.startswith("invalid/"):
            fail("%s: valid flag false but file is not under invalid/" % rel)
        if cls not in CLASSES or not entry.get("reason"):
            fail("%s: invalid entry needs class in %s and a reason" % (rel, CLASSES))
            continue
        expect = entry.get("expect", {})
        if cls == "envelope":
            if env is None:
                fail("%s: expected envelope rejection, envelope_check accepted it" % rel)
            elif env != expect.get("code"):
                fail("%s: envelope code %s, manifest says %s" % (rel, env, expect.get("code")))
            if not errors:
                fail("%s: envelope-class fixture should also fail the schema" % rel)
        elif cls == "schema":
            if env is not None:
                fail("%s: schema-class fixture is rejected by the envelope check (%s)" % (rel, env))
            if not errors:
                fail("%s: expected a schema error, found none" % rel)
            else:
                want_path, want_kw = expect.get("path"), expect.get("keyword")
                hit = any(
                    "/" + "/".join(map(str, e.absolute_path)) == want_path and e.validator == want_kw
                    for e in errors
                ) or any(
                    ("/" + "/".join(map(str, e.absolute_path))).startswith(want_path or "\0") and e.validator == want_kw
                    for e in errors
                )
                if not hit:
                    found = sorted({("/" + "/".join(map(str, e.absolute_path)), e.validator) for e in errors})[:4]
                    fail("%s: no schema error at %s with keyword %s; got %s" % (rel, want_path, want_kw, found))
        else:
            if env is not None or errors:
                fail("%s: semantic-class fixture must pass envelope and schema (env=%s, errors=%d)" % (rel, env, len(errors)))
            else:
                code = semantic_check(doc)
                if code is None:
                    fail("%s: expected a semantic failure, found none" % rel)
                elif code != expect.get("code"):
                    fail("%s: semantic code %s, manifest says %s" % (rel, code, expect.get("code")))
        if len(failures) == before:
            print("ok   invalid/%s (%s)" % (rel.split("/")[-1], cls))
    for cls in CLASSES:
        if cls not in used_classes:
            fail("no invalid fixture of class " + cls)

    # Vendoring script round trip.
    vendor = os.path.join(ROOT, "scripts", "vendor.py")
    with tempfile.TemporaryDirectory() as tmp:
        dest = os.path.join(tmp, "anno117-exchange")
        run = lambda *extra: subprocess.run(  # noqa: E731
            [sys.executable, vendor, "--dest", dest] + list(extra), capture_output=True, text=True
        )
        if run().returncode != 0:
            fail("vendor.py copy failed")
        elif not os.path.exists(os.path.join(dest, "VERSION")):
            fail("vendor.py did not write VERSION")
        else:
            if run("--check").returncode != 0:
                fail("vendor.py --check failed on a fresh copy")
            with open(os.path.join(dest, "schema", "anno117-exchange.schema.json"), "a", encoding="utf-8") as fh:
                fh.write(" ")
            if run("--check").returncode == 0:
                fail("vendor.py --check accepted a differing copy")
            else:
                print("ok   vendor.py copy, VERSION and --check")

    print("\n%d fixture(s) listed, %d failure(s)" % (len(entries), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

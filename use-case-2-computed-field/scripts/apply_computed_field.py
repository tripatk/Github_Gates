"""Create or update a Nautobot computed field from a YAML file, then verify it.

Usage:  python scripts/apply_computed_field.py computed-fields/circuit-full-name.yaml           # plan only
        python scripts/apply_computed_field.py computed-fields/circuit-full-name.yaml --apply   # make the change
Needs:  NAUTOBOT_URL and NAUTOBOT_TOKEN (the token needs write permission for --apply).
Exit:   0 = ok, 1 = a check failed, 2 = could not talk to Nautobot.
"""
import json
import sys
from pathlib import Path

import requests
import yaml
from jinja2.sandbox import SandboxedEnvironment
from jsonschema import Draft202012Validator

from common import get_all, send

SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "computed-field.schema.json"
FIELDS = ["label", "template", "weight"]    # compared and sent; 'key' identifies the field
lines = []                                  # everything we print is also kept for the report


def say(message):
    print(message)
    lines.append(message)


def render(template, circuit):
    """Render the Jinja2 template locally, the way Nautobot will: 'obj' is the circuit."""
    return SandboxedEnvironment().from_string(template).render(obj=circuit)


def run(path, apply):
    # 0. the YAML must match the schema (same idea as validate_schema.py)
    data = yaml.safe_load(open(path))
    validator = Draft202012Validator(json.loads(SCHEMA.read_text()))
    errors = sorted(validator.iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))
    for e in errors:
        say(f"❌ schema: {'.'.join(map(str, e.absolute_path)) or '(top)'}: {e.message}")
    if errors:
        return 1
    spec, cid = data["computed_field"], data["circuit_id"]

    # 1. find the circuit and read its provider and type   (manual Step 2)
    circuits = get_all("/api/circuits/circuits/", cid=cid, depth=1)
    if len(circuits) != 1:
        say(f"❌ expected exactly 1 circuit with cid '{cid}', found {len(circuits)}")
        return 1
    circuit = circuits[0]
    expected = render(spec["template"], circuit)
    say(f"circuit {cid}: provider={circuit['provider']['name']!r}, type={circuit['circuit_type']['name']!r}")
    say(f"expected value : {expected!r}")

    # 2. does the computed field already exist?  (filtered here, not on the server)
    existing = next((f for f in get_all("/api/extras/computed-fields/") if f.get("key") == spec["key"]), None)
    payload = {k: spec[k] for k in FIELDS if k in spec}
    if existing is None:
        action = "create"
    elif any(existing.get(k) != v for k, v in payload.items()):
        action = "update"
    else:
        action = "none"
    say(f"computed field '{spec['key']}': {action}")

    # 3. change it, but only with --apply                  (manual Step 5)
    if action != "none":
        if not apply:
            say("plan only (no --apply): nothing was changed")
            return 0
        if action == "create":
            send("POST", "/api/extras/computed-fields/",
                 {"content_type": spec["content_type"], "key": spec["key"], **payload})
        else:
            send("PATCH", f"/api/extras/computed-fields/{existing['id']}/", payload)
        say("✅ change applied")

    # 4. ask Nautobot what it renders and compare            (manual Step 4)
    rows = get_all("/api/circuits/circuits/", cid=cid, include="computed_fields")
    actual = rows[0].get("computed_fields", {}).get(spec["key"])
    ok = actual == expected
    say(f"{'✅' if ok else '❌'} Nautobot renders: {actual!r}")
    return 0 if ok else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--apply"]
    if len(args) != 1:
        sys.exit("usage: apply_computed_field.py <file.yaml> [--apply]")
    try:
        code = run(args[0], "--apply" in sys.argv)
    except (requests.RequestException, RuntimeError) as exc:
        say(f"❌ could not complete: {exc}")
        code = 2
    with open("computed-field-report.md", "w") as f:
        f.write("## Computed field\n\n```\n" + "\n".join(lines) + "\n```\n")
    sys.exit(code)

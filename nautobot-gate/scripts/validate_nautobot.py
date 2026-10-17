"""Stage 2 of the gate: confirm the tenant exists in Nautobot, then build a
report of that tenant's devices and IP addresses.

Usage:  python scripts/validate_nautobot.py workflows/good-example.yaml
Needs:  NAUTOBOT_URL and NAUTOBOT_TOKEN environment variables.
Output: compliance-report.md and compliance-report.json in the current folder.
Exit:   0 = pass, 1 = a check failed, 2 = could not talk to Nautobot.
"""
import json
import sys

import requests
import yaml

from common import get_all, get_tenant

# What each 'report:' entry in the workflow file means.
REPORTS = {
    "devices": {
        "path": "/api/dcim/devices/",
        "count_field": "device_count",        # the tenant record also carries a total
        "columns": ["name", "device_type", "role", "status", "location"],
    },
    "ip-addresses": {
        "path": "/api/ipam/ip-addresses/",
        "count_field": "ipaddress_count",
        "columns": ["address", "status", "dns_name", "description"],
    },
}


def cell(row, key):
    """One field as text. Related objects (status, role, ...) arrive as dicts."""
    value = row.get(key)
    if isinstance(value, dict):
        value = value.get("display") or value.get("name")
    return "-" if value in (None, "") else str(value).replace("|", "/")


def table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for row in rows:
        lines.append("| " + " | ".join(cell(row, c) for c in columns) + " |")
    return "\n".join(lines)


def run(path):
    """Check one workflow file. Returns (passed, json_record, markdown_text)."""
    with open(path) as f:
        workflow = yaml.safe_load(f)
    tenant_name = workflow["tenant"]
    record = {"file": path, "tenant": tenant_name, "status": "PASS", "sections": {}}
    md = [f"## {tenant_name}", f"_workflow file: `{path}`_", ""]

    tenant = get_tenant(tenant_name)
    if tenant is None:
        record.update(status="FAIL", reason=f"tenant '{tenant_name}' not found in Nautobot")
        md.append(f"❌ **FAIL**: tenant '{tenant_name}' not found in Nautobot")
        return False, record, "\n".join(md)

    passed = True
    for name in workflow.get("report", list(REPORTS)):       # no 'report:' key = everything
        spec = REPORTS[name]
        rows = get_all(spec["path"], tenant=tenant_name)
        expected = tenant.get(spec["count_field"])
        # Cross-check: did we collect as many rows as Nautobot says the tenant owns?
        # A mismatch usually means a pagination or filter bug.
        ok = expected is None or expected == len(rows)
        passed = passed and ok
        record["sections"][name] = {
            "count": len(rows),
            "nautobot_total": expected,
            "status": "PASS" if ok else "FAIL",
            "rows": [{c: cell(r, c) for c in spec["columns"]} for r in rows],
        }
        icon = "✅" if ok else "❌"
        md += [f"### {name}: {len(rows)} found ({icon} Nautobot reports {expected})", "",
               table(rows, spec["columns"]), ""]

    record["status"] = "PASS" if passed else "FAIL"
    return passed, record, "\n".join(md)


def main(paths):
    records, parts, all_ok = [], ["# Nautobot compliance report", ""], True
    for path in paths:
        passed, record, md = run(path)
        print(f"{'✅' if passed else '❌'} {path}: {record['status']}"
              + (f" ({record['reason']})" if "reason" in record else ""))
        for name, section in record["sections"].items():
            print(f"     {name}: {section['count']} found, Nautobot says {section['nautobot_total']}")
        records.append(record)
        parts.append(md)
        all_ok = all_ok and passed

    with open("compliance-report.json", "w") as f:
        json.dump(records, f, indent=2)
    with open("compliance-report.md", "w") as f:
        f.write("\n".join(parts) + "\n")
    return 0 if all_ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (requests.RequestException, RuntimeError) as exc:
        print(f"❌ could not complete the Nautobot check: {exc}")
        sys.exit(2)
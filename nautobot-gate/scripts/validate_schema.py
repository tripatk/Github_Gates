import sys
import json
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError

SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "workflow.schema.json"
schema = json.loads(SCHEMA.read_text())

failed = False
for path in sys.argv[1:]:
    try:
        validate(yaml.safe_load(open(path)), schema)
        print(f"✅ schema ok: {path}")
    except ValidationError as e:
        print(f"❌ {path}: {e.message}")
        failed = True

sys.exit(1 if failed else 0)
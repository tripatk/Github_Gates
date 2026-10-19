# Debugger walkthrough: use case 2, one complete run

Two files execute. Abbreviations used below:

- **A** = `scripts/apply_computed_field.py` (the main program)
- **C** = `scripts/common.py` (the Nautobot helper functions)

**Sample data used.** I recorded this run with Python's tracing hook, so every line order and value below is real, not guessed. Nautobot was replaced by a fake that holds your circuit:

- The circuit `141SING177360357239` exists (provider *Tata Communications*, type *Transit*).
- The computed field `circuit_full_name` does **not** exist yet, so we see the *create* path.
- The fake returns the computed-field list in **two pages**, so you can watch the paging loop. Real Nautobot would return one page for a list this small.

**How to read each step.** *Code* is the exact line. *What happens* covers syntax and meaning. *Next* says why execution goes where it goes. *State* lists the variables and memory after the line has run.

---

## PART 0. Before Python starts

The workflow's last shell command is:
```
cd use-case-2-computed-field
python scripts/apply_computed_field.py "computed-fields/circuit-full-name.yaml" --apply
```
The environment already holds `NAUTOBOT_URL` and `NAUTOBOT_TOKEN` (GitHub copied them from your secrets).

The operating system starts the Python interpreter and gives it:
- `sys.argv = ["scripts/apply_computed_field.py", "computed-fields/circuit-full-name.yaml", "--apply"]`
- `sys.path[0]` = the folder of the script file, i.e. `.../use-case-2-computed-field/scripts`. This matters later: it is why `import common` is found.
- `__name__ = "__main__"` for the file being run directly.

Execution starts at the top of A.

---

## PART 1. A is read top to bottom (nothing runs yet except definitions)

### Step 1: `A:1-7`
```python
"""Create or update a Nautobot computed field from a YAML file, then verify it. ..."""
```
- **What happens:** a string at the very top of a file is the *module docstring*. It is evaluated and stored in `__doc__`. It does nothing else.
- **Next:** falls through to the next statement.
- **State:** `__doc__` = that text.

### Step 2: `A:8, 9, 10`
```python
import json
import sys
from pathlib import Path
```
- **What happens:** `import json` loads the standard library module and binds the name `json` in A's namespace. `from pathlib import Path` loads the module but binds only the class `Path`.
- **Next:** next line.
- **State:** names `json`, `sys`, `Path` now exist.

### Step 3: `A:12, 13, 14, 15`
```python
import requests
import yaml
from jinja2.sandbox import SandboxedEnvironment
from jsonschema import Draft202012Validator
```
- **What happens:** the same mechanism for installed packages (they exist because `pip install -r requirements.txt` ran). If one were missing, Python would stop here with `ModuleNotFoundError` and the job would go red before doing any work.
- **Next:** next line.
- **State:** adds `requests`, `yaml`, `SandboxedEnvironment`, `Draft202012Validator`.

### Step 4: `A:17`  >>> JUMP into common.py
```python
from common import get_all, send
```
- **What happens:** Python looks for a module called `common`. It searches the folders in `sys.path`, starting with `sys.path[0]`, which is `scripts/`. It finds `scripts/common.py`.
- **Next:** Python does **not** copy individual functions. It **runs the whole of C from the top** (steps 5 to 9), then comes back and binds only the two names asked for.

### Step 5: `C:1-6`
```python
"""Small Nautobot REST helpers shared by the validation scripts."""
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
```
- **What happens:** docstring, then C's own imports. `requests` is imported again, which is cheap: Python reuses the already-loaded module from its cache.
- **State:** C's namespace has `os`, `requests`, `HTTPAdapter`, `Retry`.

### Step 6: `C:9`
```python
def make_session():
```
- **What happens:** a `def` statement runs the moment Python reaches it, but it only *creates a function object* and binds the name `make_session`. The body (lines 10-22) is **not** executed now.
- **State:** `make_session` is a function in memory.

### Step 7: `C:25`
```python
def get_all(path, **params):
```
- **What happens:** same thing. `**params` means "collect any extra keyword arguments into a dictionary called `params`".
- **State:** `get_all` is a function object.

### Step 8: `C:39` and `C:45`
```python
def get_tenant(name): ...
def send(method, path, payload): ...
```
- **What happens:** two more function objects. `get_tenant` belongs to use case 1's needs and is unused here. `send` is the writer.
- **Next:** end of file, so the module is done and execution returns to A.
- **State:** module `common` now lives in memory with 4 functions.

### Step 9: back at `A:17` (finishing the import)
- **What happens:** Python takes the names `get_all` and `send` out of module `common` and binds them in A's namespace.
- **State:** A's namespace has `get_all` and `send`, pointing at the very same function objects from step 7 and 8.

### Step 10: `A:19, 20, 21`
```python
SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "computed-field.schema.json"
FIELDS = ["label", "template", "weight"]
lines = []
```
- **What happens:**
  - `__file__` is the script path. `.resolve()` makes it absolute, `.parent` gives `scripts/`, `.parent` again gives the use-case folder. The `/` operator on a `Path` joins path pieces.
  - `FIELDS` is a list of the three settings that get compared and sent.
  - `lines = []` is an empty list that will collect everything printed, for the report.
- **State:**
  - `SCHEMA = .../use-case-2-computed-field/schema/computed-field.schema.json`
  - `FIELDS = ['label', 'template', 'weight']`
  - `lines = []`

### Step 11: `A:24`, `A:29`, `A:34`
```python
def say(message): ...
def render(template, circuit): ...
def run(path, apply): ...
```
- **What happens:** three more function objects, none executed yet.
- **State:** A now knows `say`, `render`, `run`.

### Step 12: `A:86`
```python
if __name__ == "__main__":
```
- **What happens:** `__name__` is `"__main__"` because the file was started directly (Part 0), so the condition is True. If another file had imported A, this block would be skipped. That is the purpose of this idiom.
- **Next:** enter the block.

### Step 13: `A:87`
```python
    args = [a for a in sys.argv[1:] if a != "--apply"]
```
- **What happens:** `sys.argv[1:]` is everything after the script name: `['computed-fields/circuit-full-name.yaml', '--apply']`. The list comprehension keeps each item *except* `--apply`.
- **State:** `args = ['computed-fields/circuit-full-name.yaml']`

### Step 14: `A:88`
```python
    if len(args) != 1:
        sys.exit("usage: ...")
```
- **What happens:** the length is 1, so `1 != 1` is False.
- **Next:** the line under the `if` is **skipped**. Had it been True, the program would print the usage text and stop.

### Step 15: `A:90-91`  >>> JUMP into run()
```python
    try:
        code = run(args[0], "--apply" in sys.argv)
```
- **What happens:** `try:` starts a protected block. Python evaluates the arguments first: `args[0]` is the YAML path, and `"--apply" in sys.argv` is `True` (the full list still contains it). Then it calls `run`.
- **Next:** control goes into `run`; the assignment to `code` waits for `run` to return.
- **State:** a new *frame* (a private set of variables) is created for `run`: `path = 'computed-fields/circuit-full-name.yaml'`, `apply = True`.

---

## PART 2. Inside `run()`

### Step 16: `A:36`
```python
    data = yaml.safe_load(open(path))
```
- **What happens:** `open(path)` opens the file (relative to the current folder, which is `use-case-2-computed-field/`). `yaml.safe_load` parses the YAML into plain Python objects. "safe" means it can never build arbitrary objects from the file.
- **State:**
  ```
  data = {'name': 'circuit-full-name',
          'circuit_id': '141SING177360357239',
          'computed_field': {'content_type': 'circuits.circuit', 'key': 'circuit_full_name',
                             'label': 'Circuit Full Name',
                             'template': '{{ obj.cid }}-{{ obj.circuit_type.name }}-{{ obj.provider.name }}',
                             'weight': 100}}
  ```

### Step 17: `A:37`
```python
    validator = Draft202012Validator(json.loads(SCHEMA.read_text()))
```
- **What happens, from the inside out:** `SCHEMA.read_text()` reads the schema file into a string. `json.loads` parses it into a dict. `Draft202012Validator(...)` builds an object that can check data against that dict.
- **State:** `validator` is ready. Nothing is checked yet.

### Step 18: `A:38`
```python
    errors = sorted(validator.iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))
```
- **What happens:** `iter_errors(data)` yields every rule violation. `sorted(..., key=...)` collects them in order of where they occur in the file. The `lambda` is a tiny anonymous function that gives each error its sort key.
- **Next:** the YAML satisfies every rule (content type is exactly `circuits.circuit`, key matches `^[a-z][a-z0-9_]*$`, template contains `{{ }}`, weight is an integer).
- **State:** `errors = []`

### Step 19: `A:39`
```python
    for e in errors:
        say(...)
```
- **What happens:** the list is empty, so the loop body (line 40) runs **zero times**.

### Step 20: `A:41`
```python
    if errors:
        return 1
```
- **What happens:** an empty list is falsy, so the condition is False and `return 1` is **skipped**. This is the first of several possible early exits (see the jump map at the end).

### Step 21: `A:43`
```python
    spec, cid = data["computed_field"], data["circuit_id"]
```
- **What happens:** a tuple assignment. The right side builds a pair of values and the left side unpacks it into two names. `data["circuit_id"]` is a dictionary lookup by key.
- **State:**
  - `spec = {'content_type': 'circuits.circuit', 'key': 'circuit_full_name', 'label': ..., 'template': ..., 'weight': 100}`
  - `cid = '141SING177360357239'`

### Step 22: `A:46`  >>> JUMP into get_all (call 1 of 3)
```python
    circuits = get_all("/api/circuits/circuits/", cid=cid, depth=1)
```
- **What happens:** `run` pauses on this line. Python calls `get_all`: `/api/circuits/circuits/` fills the parameter `path`, and the keyword arguments `cid=` and `depth=` are gathered by `**params`.
- **State inside the new frame:**
  - `path = '/api/circuits/circuits/'`
  - `params = {'cid': '141SING177360357239', 'depth': 1}`

### Step 23: `C:27`  >>> JUMP into make_session
```python
    session, base = make_session()
```
- **What happens:** `get_all` needs an authenticated connection, so it calls `make_session()` first. It will return a two-item tuple, unpacked into two names.

### Step 24: `C:11`
```python
    url = os.environ.get("NAUTOBOT_URL", "").rstrip("/")
```
- **What happens:** `os.environ` is the dictionary of environment variables. `.get(key, default)` returns the value, or `""` if missing. `.rstrip("/")` removes a trailing slash so later string joins don't produce `//`.
- **State:** `url = 'https://demo.nautobot.com'`

### Step 25: `C:12`
```python
    token = os.environ.get("NAUTOBOT_TOKEN", "")
```
- **State:** `token` = the 40-character secret. It exists only in memory in this frame.

### Step 26: `C:13`
```python
    if not url or not token:
        raise RuntimeError(...)
```
- **What happens:** both are non-empty, so `not url` and `not token` are False and the `raise` on line 14 is **skipped**. Had a secret been missing, a `RuntimeError` would shoot upward through every caller until the `except` at `A:92` catches it, and the program would exit with code 2.

### Step 27: `C:16`
```python
    session = requests.Session()
```
- **What happens:** creates a `Session` object: it keeps default headers and reuses TCP connections between requests.
- **State:** `session` = a new, empty `Session`.

### Step 28: `C:17`
```python
    session.headers.update({"Authorization": f"Token {token}", "Accept": "application/json"})
```
- **What happens:** `f"Token {token}"` is an f-string that inserts the token into the text. `headers.update` adds both headers to every request this session makes later.
- **State:** `session.headers` now includes `Authorization: Token xxxxxxxx...` and `Accept: application/json`.

### Step 29: `C:19`
```python
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
```
- **What happens:** builds a retry *policy*: retry up to 3 times when the server answers with one of those codes, waiting a little longer each time. Nothing is sent yet.
- **State:** `retry` is a policy object.

### Step 30: `C:20-21`
```python
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
```
- **What happens:** a session picks an *adapter* by the URL's prefix. These two lines attach the retry policy to every `https://` and `http://` URL.

### Step 31: `C:22`  >>> RETURN to get_all
```python
    return session, url
```
- **What happens:** returns a tuple `(session, 'https://demo.nautobot.com')`. The `make_session` frame is destroyed: `url`, `token` and `retry` vanish. The `session` object survives because it was returned.
- **Next:** back to `C:27`, where the tuple is unpacked.
- **State in get_all:** `session` = the Session, `base = 'https://demo.nautobot.com'`.

### Step 32: `C:28`
```python
    params.setdefault("limit", 100)
```
- **What happens:** `setdefault` adds a key *only if it is missing*. The caller didn't pass `limit`, so it is added.
- **State:** `params = {'cid': '141SING177360357239', 'depth': 1, 'limit': 100}`

### Step 33: `C:29`
```python
    url, results = f"{base}{path}", []
```
- **State:**
  - `url = 'https://demo.nautobot.com/api/circuits/circuits/'`
  - `results = []`

### Step 34: `C:30`  (loop test, pass 1)
```python
    while url:
```
- **What happens:** a non-empty string is truthy, so the loop body runs.

### Step 35: `C:31`  >>> network request
```python
        response = session.get(url, params=params, timeout=20)
```
- **What happens:** the only line that touches the network. `requests` appends `params` as a query string and sends:
  ```
  GET /api/circuits/circuits/?cid=141SING177360357239&depth=1&limit=100
  Authorization: Token ...
  ```
  `timeout=20` means: give up after 20 seconds with no answer.
- **State:** `response = <Response [200]>`

### Step 36: `C:32`
```python
        response.raise_for_status()
```
- **What happens:** raises an exception for 4xx and 5xx codes (a wrong token gives 403, a missing path gives 404). Here the status is 200, so nothing happens.
- **Next:** if it had raised, execution would jump out of `get_all` and out of `run` to `A:92`.

### Step 37: `C:33`
```python
        body = response.json()
```
- **What happens:** parses the JSON text of the reply into Python objects.
- **State:**
  ```
  body = {'next': None,
          'results': [{'id': 'c-1', 'cid': '141SING177360357239', 'status': {'display': 'Active'},
                       'provider': {'id': 'p-1', 'name': 'Tata Communications'},
                       'circuit_type': {'id': 't-1', 'name': 'Transit'}}]}
  ```
  Because of `depth=1`, `provider` and `circuit_type` arrive as full objects with a `name`, not as bare ids.

### Step 38: `C:34`
```python
        results.extend(body["results"])
```
- **What happens:** `extend` appends every item of the given list to `results`.
- **State:** `results = [ {the circuit} ]`

### Step 39: `C:35`
```python
        url, params = body.get("next"), None
```
- **What happens:** `body.get("next")` returns the next-page link, or `None` when there is none. `params` is reset to `None` because a `next` link already contains the filters in its query string.
- **State:** `url = None`, `params = None`

### Step 40: `C:30`  (loop test again)  >>> exit loop
```python
    while url:
```
- **What happens:** `None` is falsy, so the loop ends. **Jump:** execution skips the whole loop body and continues *after* it.

### Step 41: `C:36`  >>> RETURN to run()
```python
    return results
```
- **What happens:** hands the list back. The `get_all` frame (`session`, `base`, `body`, `response`, ...) is destroyed.
- **Next:** back in `run`, at `A:46`, the paused assignment completes.
- **State in run:** `circuits = [ {the circuit} ]`  (a list of exactly one dict)

### Step 42: `A:47`
```python
    if len(circuits) != 1:
        say(f"❌ expected exactly 1 circuit ...")
        return 1
```
- **What happens:** `len(circuits)` is 1, so the condition is False and the three lines below are **skipped**. This is the check that proves your circuit exists in Nautobot. With 0 results the run would end here with exit code 1.

### Step 43: `A:50`
```python
    circuit = circuits[0]
```
- **What happens:** takes the first and only element out of the list.
- **State:** `circuit = {'id': 'c-1', 'cid': '141SING177360357239', 'status': ..., 'provider': {...}, 'circuit_type': {...}}`

### Step 44: `A:51`  >>> JUMP into render()
```python
    expected = render(spec["template"], circuit)
```
- **State inside render:** `template = '{{ obj.cid }}-{{ obj.circuit_type.name }}-{{ obj.provider.name }}'`, `circuit` = the dict.

### Step 45: `A:31`
```python
    return SandboxedEnvironment().from_string(template).render(obj=circuit)
```
- **What happens**, chained left to right:
  1. `SandboxedEnvironment()` creates a restricted Jinja2 engine. It refuses unsafe operations such as reaching into Python internals.
  2. `.from_string(template)` compiles the text into a template object.
  3. `.render(obj=circuit)` evaluates it with the variable `obj` bound to the circuit.
- **How each `{{ }}` resolves:** Jinja's `.` first tries an attribute, then falls back to a dictionary key.
  - `obj.cid` → `circuit['cid']` = `141SING177360357239`
  - `obj.circuit_type.name` → `circuit['circuit_type']['name']` = `Transit`
  - `obj.provider.name` → `circuit['provider']['name']` = `Tata Communications`
  - the text between `}}` and `{{` is the literal `-`
- **Next:** returns the finished string to `A:51`.
- **State in run:** `expected = '141SING177360357239-Transit-Tata Communications'`

### Step 46: `A:52`  >>> JUMP into say()
```python
    say(f"circuit {cid}: provider={circuit['provider']['name']!r}, type={circuit['circuit_type']['name']!r}")
```
- **What happens:** builds the message first. `!r` inserts the value with Python quote marks (`'Transit'`). Then calls `say`.

### Step 47: `A:25-26`
```python
    print(message)
    lines.append(message)
```
- **What happens:** `print` writes to the terminal (the GitHub log). `lines.append` also stores the message in the module-level list from step 10, for the report file. `say` returns `None` and its frame is destroyed.
- **State:** `lines` has 1 string. Terminal shows: `circuit 141SING177360357239: provider='Tata Communications', type='Transit'`

### Step 48: `A:53`  (same mechanism as step 46-47)
```python
    say(f"expected value : {expected!r}")
```
- **State:** `lines` has 2 strings. Terminal shows: `expected value : '141SING177360357239-Transit-Tata Communications'`

### Step 49: `A:56`  >>> JUMP into get_all (call 2 of 3)
```python
    existing = next((f for f in get_all("/api/extras/computed-fields/") if f.get("key") == spec["key"]), None)
```
- **What happens:**
  - The expression is a **generator expression** `(f for f in ... if ...)` wrapped in `next(gen, None)`.
  - Python rule: the first iterable of a generator expression is evaluated **immediately**, so `get_all(...)` runs now, fully, before any filtering starts.
  - This is a list request with no filters, so `params = {}`.

### Steps 50-57: inside get_all, call 2. Same lines as steps 23-41, with these differences:
- `C:27` → a **new** `make_session()` call (steps 24-31 run again, creating a new Session). Sessions are not reused between calls.
- `C:28` → `params = {'limit': 100}`
- `C:29` → `url = 'https://demo.nautobot.com/api/extras/computed-fields/'`
- **Loop pass 1** (`C:30-35`):
  - request `GET .../api/extras/computed-fields/?limit=100`
  - `body = {'next': 'https://demo.nautobot.com/api/extras/computed-fields/?limit=1&offset=1', 'results': [{'id': 'f-0', 'key': 'some_other_field', ...}]}`
  - `results = [ {some_other_field} ]`
  - `C:35`: `url = '...?limit=1&offset=1'`, `params = None`
- **Loop test** (`C:30`): `url` is a non-empty string, so the loop **repeats**. *This is the jump backward that makes get_all a "get all" function.*
- **Loop pass 2** (`C:31-35`):
  - request goes to exactly the `next` URL, with no extra params
  - `body = {'next': None, 'results': []}`
  - `results.extend([])` adds nothing
  - `url = None`
- **Loop test:** `None` → exit. `C:36` returns `[ {some_other_field} ]`.

### Step 58: `A:56`  (the generator now runs)
- **What happens:** `next(...)` pulls items from the generator one at a time. The generator takes the first `f`:
  - `f = {'id': 'f-0', 'key': 'some_other_field', ...}`
  - `f.get("key") == spec["key"]` → `'some_other_field' == 'circuit_full_name'` → False, so `f` is not yielded
  - the list is exhausted, so the generator ends without yielding anything
- **Next:** because it yielded nothing, `next` returns its **default**, the second argument `None`.
- **State in run:** `existing = None`

### Step 59: `A:57`
```python
    payload = {k: spec[k] for k in FIELDS if k in spec}
```
- **What happens:** a dictionary comprehension. It loops over `FIELDS` (`label`, `template`, `weight`), keeps each key that exists in `spec`, and builds a dictionary. `content_type` and `key` are deliberately **not** in `FIELDS`: they identify the field and aren't compared or patched.
- **State:** `payload = {'label': 'Circuit Full Name', 'template': '{{ obj.cid }}-{{ obj.circuit_type.name }}-{{ obj.provider.name }}', 'weight': 100}`

### Step 60: `A:58-59`  (an if / elif / else chain)
```python
    if existing is None:
        action = "create"
    elif any(existing.get(k) != v for k, v in payload.items()):
        action = "update"
    else:
        action = "none"
```
- **What happens:** `existing is None` is True, so the first branch runs and sets `action = "create"`.
- **Jump:** Python runs **exactly one** branch of an if/elif/else chain, then continues after the whole chain. It skips lines 60-63 entirely, including the `elif` condition (it is not even evaluated).
- **State:** `action = 'create'`

### Step 61: `A:64`
```python
    say(f"computed field '{spec['key']}': {action}")
```
- **State:** terminal shows `computed field 'circuit_full_name': create`. `lines` has 3 strings.

### Step 62: `A:67`
```python
    if action != "none":
```
- **What happens:** `'create' != 'none'` is True. We enter the block.
- **Note (alternate path):** in your real "none" run this is False, and execution **jumps over lines 68-76** straight to line 79. That is why your earlier live run printed no "change applied" line.

### Step 63: `A:68`
```python
        if not apply:
```
- **What happens:** `apply` is `True` (from `"--apply" in sys.argv`, step 15), so `not apply` is False and the two lines below it (the plan-only message and `return 0`) are **skipped**.
- **Note (alternate path):** without `--apply` (a PR, or your plan-only local run), this is True: it prints "plan only..." and `return 0` ends `run` right here. Nothing is written.

### Step 64: `A:71`
```python
        if action == "create":
```
- **What happens:** True, so the create branch runs. The `else:` at line 74 (the PATCH branch) will be skipped.

### Step 65: `A:72-73`  >>> JUMP into send()
```python
            send("POST", "/api/extras/computed-fields/",
                 {"content_type": spec["content_type"], "key": spec["key"], **payload})
```
- **What happens:** the third argument is a dictionary literal built first: `content_type` and `key` from `spec`, then `**payload` **unpacks** the three payload items into the same dictionary.
- **State inside send:**
  - `method = 'POST'`
  - `path = '/api/extras/computed-fields/'`
  - `payload = {'content_type': 'circuits.circuit', 'key': 'circuit_full_name', 'label': 'Circuit Full Name', 'template': '...', 'weight': 100}`

### Step 66: `C:47`
```python
    session, base = make_session()
```
- **What happens:** the full `make_session` sequence runs again (steps 24-31) to build a new authenticated session.

### Step 67: `C:48`  >>> network request
```python
    response = session.request(method, f"{base}{path}", json=payload, timeout=20)
```
- **What happens:** a generic request with the method given as text. `json=payload` converts the dictionary to JSON and sets `Content-Type: application/json`. On the wire:
  ```
  POST /api/extras/computed-fields/
  {"content_type":"circuits.circuit","key":"circuit_full_name","label":"Circuit Full Name", ...}
  ```
  **This is the line that changes Nautobot's data.**
- **State:** `response = <Response [201]>`. 201 means "Created".

### Step 68: `C:49`
```python
    if not response.ok:
        raise RuntimeError(...)
```
- **What happens:** `response.ok` is True for any status below 400. `not True` is False, so the `raise` (line 50) is **skipped**.
- **Note (alternate path):** with a read-only token, Nautobot answers 403. Then `raise` runs and the error flies up past `run` to `A:92`, which prints "could not complete" and sets `code = 2`.

### Step 69: `C:51`  >>> RETURN to run()
```python
    return response.json()
```
- **State:** returns the created object (your fields plus the new `id`). Back at `A:72` the result is **discarded**: the call is a bare statement, not assigned to anything, because `run` doesn't need it.

### Step 70: `A:74-75` skipped, `A:76`
```python
        else:
            send("PATCH", ...)       # lines 74-75 are skipped
        say("✅ change applied")      # line 76
```
- **What happens:** since the `if` branch ran, the `else` branch is skipped and execution continues with line 76, which is indented only as far as the outer `if` (line 67), so it belongs to that block.
- **State:** terminal shows `✅ change applied`. `lines` has 4 strings.

### Step 71: `A:79`  >>> JUMP into get_all (call 3 of 3)
```python
    rows = get_all("/api/circuits/circuits/", cid=cid, include="computed_fields")
```
- **What happens:** like step 22, with a different parameter. The same loop and a new session:
  - `params = {'cid': '141SING177360357239', 'include': 'computed_fields', 'limit': 100}`
  - one request: `GET /api/circuits/circuits/?cid=...&include=computed_fields&limit=100`
  - `include=computed_fields` tells Nautobot to add each computed field's **rendered value** to every circuit.
  - one page (`next` is `None`), so the loop runs once.
- **State in run:** `rows = [ {circuit..., 'computed_fields': {'circuit_full_name': '141SING177360357239-Transit-Tata Communications'}} ]`

### Step 72: `A:80`
```python
    actual = rows[0].get("computed_fields", {}).get(spec["key"])
```
- **What happens:** `rows[0]` is the circuit. `.get("computed_fields", {})` returns that sub-dictionary, or an empty one if absent. `.get(spec["key"])` looks up `'circuit_full_name'`.
- **State:** `actual = '141SING177360357239-Transit-Tata Communications'`

### Step 73: `A:81`
```python
    ok = actual == expected
```
- **What happens:** string comparison. The left value came from **Nautobot**, the right from **your local Jinja2 render** in step 45. Equal means your intended field is what Nautobot actually displays.
- **State:** `ok = True`

### Step 74: `A:82`
```python
    say(f"{'✅' if ok else '❌'} Nautobot renders: {actual!r}")
```
- **What happens:** `'✅' if ok else '❌'` is a one-line conditional expression. Terminal shows `✅ Nautobot renders: '141SING177360357239-Transit-Tata Communications'`. `lines` has 5 strings.

### Step 75: `A:83`  >>> RETURN to module level
```python
    return 0 if ok else 1
```
- **What happens:** another conditional expression. `ok` is True, so the value is `0`.
- **Next:** `run`'s frame is destroyed (`data`, `spec`, `circuit`, `expected`, `payload`, ... all gone). The paused call at `A:91` completes.
- **State at module level:** `code = 0`

---

## PART 3. Back at the bottom of the file

### Step 76: `A:92-94` skipped
```python
    except (requests.RequestException, RuntimeError) as exc:
        say(f"❌ could not complete: {exc}")
        code = 2
```
- **Why jump:** the `try` body (line 91) finished **without raising**, so Python skips the whole `except` block and continues after it. This is the only way an error can set exit code 2.

### Step 77: `A:95-96`
```python
    with open("computed-field-report.md", "w") as f:
        f.write("## Computed field\n\n```\n" + "\n".join(lines) + "\n```\n")
```
- **What happens:** `open(..., "w")` creates the file (or empties an existing one). `"\n".join(lines)` glues the 5 strings from `lines` together with line breaks. `f.write(...)` writes the text.
- **State:** the file `computed-field-report.md` now exists in the folder.

### Step 78: `A:95` (cleanup)
- **What happens:** when the indented block ends, the `with` statement automatically **closes the file**, even if the block had crashed. That is why `with` is preferred over a bare `open`.

### Step 79: `A:97`  >>> END
```python
    sys.exit(code)
```
- **What happens:** raises a special `SystemExit(0)`. Python catches it at the top, flushes output, and ends the process with status **0**.
- **Result:** the shell reports success to GitHub, so the step is green. The next workflow step (`cat computed-field-report.md >> $GITHUB_STEP_SUMMARY`) copies the report to the run summary page.

---

## Jump map: other routes the same code can take

| Condition | Line | Where control jumps | Exit code |
|---|---|---|---|
| YAML breaks the schema | `A:41` | `return 1` ends `run` early | 1 |
| Circuit not found (0 or 2+ rows) | `A:47` | `return 1` ends `run` early | 1 |
| Token or URL missing | `C:13` | `raise` leaves `make_session`, `get_all` and `run`, lands at `A:92` | 2 |
| Wrong token (HTTP 401/403), server error | `C:32` | `raise_for_status` raises, lands at `A:92` | 2 |
| Read-only token, write refused | `C:49` | `raise RuntimeError`, lands at `A:92` | 2 |
| No `--apply`, change needed | `A:68` | prints "plan only", `return 0` | 0 |
| Field already identical (`none`) | `A:67` | jumps over lines 68-76 straight to `A:79` | 0 |
| Field exists but differs (`update`) | `A:71` | skips the POST, runs the `else` at `A:75` (PATCH) | 0 |
| Nautobot renders something different | `A:81-83` | `ok = False`, `return 1` | 1 |

## Memory picture at the peak (just before step 75)

```
module level (A)   : SCHEMA, FIELDS, lines [5 strings], args, code (not set yet)
run() frame        : path, apply=True, data, validator, errors=[], spec, cid, circuits, circuit,
                     expected, existing=None, payload, action='create', rows, actual, ok=True
```
Everything inside `get_all`, `make_session`, `send`, `render` and `say` came and went: each call creates a private frame that is destroyed on return. Only `lines` (module-level) and Nautobot's own database kept anything.

## Try it yourself with Python's built-in debugger

Use **plan-only** (no `--apply`) so nothing is written to Nautobot:
```
cd use-case-2-computed-field && source .venv/bin/activate
export NAUTOBOT_URL=https://demo.nautobot.com NAUTOBOT_TOKEN=<token>
python -m pdb scripts/apply_computed_field.py computed-fields/circuit-full-name.yaml
```
At the `(Pdb)` prompt:

| Key | Meaning |
|---|---|
| `n` | execute this line, stay in the current function (step over) |
| `s` | step *into* the function called on this line (so `s` on `A:46` jumps into `get_all`) |
| `r` | run until the current function returns |
| `p variable` | print a variable, e.g. `p circuits` or `p expected` |
| `l` | list the code around the current line |
| `w` | where am I? Shows the call stack (A → C → ...) |
| `b common.py:31` | set a breakpoint at that line |
| `c` | continue to the next breakpoint |
| `q` | quit |

Press `n` and `s` at the lines named in each step above to reproduce this walkthrough with your live data.

---

## PART 4. The same program on GitHub: your real log, mapped to the steps

This part uses the log you downloaded (`0_computed-field.txt`): the `uc2-computed-field` run for commit `2c5b50b` on 18 Oct 2026, started 03:57 UTC. Your field already existed, so GitHub ran the **"none" path**, not the create path of Parts 1 to 3. I also traced that path locally. Both agree.

### 4.1 The log, in order

| Time (UTC) | What the log shows | Where it fits in this document |
|---|---|---|
| 03:57:12 | Runner image, `GITHUB_TOKEN Permissions: Contents: read, Metadata: read, Packages: read` | GitHub picks a fresh Ubuntu 24.04 machine and gives the job a read-only built-in token |
| 03:57:13 | `Run actions/checkout@v4`, with `env:` showing `NAUTOBOT_URL: ***`, `NAUTOBOT_TOKEN: ***`, `TARGET: computed-fields/circuit-full-name.yaml`, `FLAGS: --apply` | Part 0. The workflow's `env:` block was evaluated **before** any step ran. `FLAGS: --apply` proves the expression `github.event_name == 'push'` came out true |
| 03:57:14 | `fetch ... origin +2c5b50b...:refs/remotes/origin/main`, `git checkout ... -B main` | Your repo is copied onto the runner at exactly commit `2c5b50b` |
| 03:57:15 to 18 | `Run actions/setup-python@v5`, "Successfully set up CPython (3.11.17)", "Cache hit ... Cache restored successfully" | Python 3.11 installed; the pip download cache restored using `use-case-2-computed-field/requirements.txt` as the cache key |
| 03:57:18 to 22 | `Run pip install -r requirements.txt` installing requests, pyyaml, jsonschema, jinja2, pytest, requests-mock | Part 1, steps 2 and 3. These installs are why the `import` lines at `A:8-15` succeed |
| 03:57:22 | `Run python scripts/apply_computed_field.py "$TARGET" $FLAGS` | Part 0. `$TARGET` and `$FLAGS` expand to the values in the `env:` block, giving exactly `--apply` |
| 03:57:24.113 | `circuit 141SING177360357239: provider='Tata Communications', type='Transit'` | Step 46-47 (`A:52`) |
| 03:57:24.113 | `expected value : '141SING177360357239-Transit-Tata Communications'` | Step 48 (`A:53`) |
| 03:57:24.113 | `computed field 'circuit_full_name': none` | Step 61 (`A:64`), with `action = "none"` |
| 03:57:24.113 | `✅ Nautobot renders: '141SING177360357239-Transit-Tata Communications'` | Step 74 (`A:82`) |
| 03:57:24.157 | `Run cat computed-field-report.md >> "$GITHUB_STEP_SUMMARY" || true` | The step after the script: copies the report to the run summary page |
| 03:57:24 to 25 | `Post job cleanup`, "Cache saved", git config cleanup, "Cleaning up orphan processes" | GitHub tidies up. The job ends with success |

Total job time was about 13 seconds. The script itself took about 1.4 seconds.

### 4.2 What changes in the steps for the "none" path

Steps 1 to 59 are identical. Only the part after the field list was fetched differs. The real code path (confirmed locally) is:

| Step | Line | What happens in the "none" case |
|---|---|---|
| 58 | `A:56` | `get_all` returns the existing field. The generator finds `f.get("key") == 'circuit_full_name'` → True, so it yields it. `existing = {'id': ..., 'key': 'circuit_full_name', 'label': 'Circuit Full Name', 'template': '...', 'weight': 100, ...}` |
| 59 | `A:57` | `payload` is built exactly as before |
| 60a | `A:58` | `if existing is None:` → **False**. The `create` branch is skipped |
| 60b | `A:60` | `elif any(existing.get(k) != v for k, v in payload.items()):` is **now evaluated**. It compares `label`, `template` and `weight` of the existing field with the YAML values one by one. Every comparison is False (they are equal), so `any(...)` is False |
| 60c | `A:63` | The `else` branch runs: `action = "none"` |
| 61 | `A:64` | prints `computed field 'circuit_full_name': none` |
| 62 | `A:67` | `if action != "none":` → **False**. Lines 68 to 76 are skipped as a block: no `apply` check, no `send()`, no POST, no "change applied" message |
| 71 | `A:79` | execution **jumps straight to** the read-back of Nautobot's rendered value |
| 72 to 75 | `A:80-83` | same as before. `ok = True`, exit code 0 |

Compared with the create run:
- The `send()` function is **never called**.
- `make_session` runs 3 times instead of 4.
- Only 3 HTTP requests are made, and all are GET.

This is what makes the script idempotent: you can run it a hundred times and it only writes the first time (or when the YAML changes).

### 4.3 What the log shows that is worth knowing

1. **Secrets stayed hidden.** `NAUTOBOT_URL` and `NAUTOBOT_TOKEN` appear as `***` everywhere in the log. GitHub masks any secret value it knows about, so even an accidental print of the token would be replaced.
2. **The token is read-only for the repo.** `GITHUB_TOKEN Permissions: Contents: read` is GitHub's own token for repo access. It is separate from your Nautobot token. Adding `permissions: contents: read` at the top of the workflow file would make this explicit instead of relying on the repo's default setting. It is optional.
3. **A warning, not an error.** At the bottom: *"Node.js 20 is deprecated. The following actions ... actions/checkout@v4, actions/setup-python@v5 ... are being forced to run on Node.js 24."* The run still passed. Later, check each action's release page for a newer major version and update the `@v4` and `@v5` in the workflow files.
4. **Install time.** `pytest` and `requests-mock` are installed although use case 2's workflow doesn't run tests yet. They cost about a second. They will be used once offline tests are added.
5. **This log only covers the "none" path.** The create and update paths have been tested with a mocked Nautobot but have not yet run on GitHub.

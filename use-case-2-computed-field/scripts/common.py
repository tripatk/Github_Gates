"""Small Nautobot REST helpers shared by the validation scripts."""
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def make_session():
    """Build a requests session with the token header and automatic retries."""
    url = os.environ.get("NAUTOBOT_URL", "").rstrip("/")
    token = os.environ.get("NAUTOBOT_TOKEN", "")
    if not url or not token:
        raise RuntimeError("Set the NAUTOBOT_URL and NAUTOBOT_TOKEN environment variables first")

    session = requests.Session()
    session.headers.update({"Authorization": f"Token {token}", "Accept": "application/json"})
    # The public demo can be slow or flaky: retry a few times before giving up.
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session, url


def get_all(path, **params):
    """GET a list endpoint and follow the 'next' links until every row is collected."""
    session, base = make_session()
    params.setdefault("limit", 100)
    url, results = f"{base}{path}", []
    while url:
        response = session.get(url, params=params, timeout=20)
        response.raise_for_status()
        body = response.json()
        results.extend(body["results"])
        url, params = body.get("next"), None   # 'next' already carries the query string
    return results


def get_tenant(name):
    """Return the tenant with exactly this name, or None if Nautobot has no such tenant."""
    found = get_all("/api/tenancy/tenants/", name=name)
    return found[0] if found else None


def send(method, path, payload):
    """POST or PATCH JSON to Nautobot and return the response body."""
    session, base = make_session()
    response = session.request(method, f"{base}{path}", json=payload, timeout=20)
    if not response.ok:
        raise RuntimeError(f"{method} {path} -> HTTP {response.status_code}: {response.text[:300]}")
    return response.json()

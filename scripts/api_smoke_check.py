"""Verify final same-origin demo APIs and locally bundled API documentation."""
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent.parent
values = dict(line.split("=", 1) for line in (root / ".env").read_text(encoding="utf-8").splitlines() if line and not line.startswith("#") and "=" in line)
origin = "http://127.0.0.1:" + values.get("FRONTEND_PORT", "3000")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def get(path):
    try:
        response = opener.open(origin + path, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()

for kind, count in [("ads", 10), ("products", 8), ("shops", 6)]:
    status, headers, content = get(f"/api/v1/{kind}/")
    assert status == 200
    data = json.loads(content)
    assert data["count"] == count and data["source_kind"] == "demo"
    assert "no-store" in headers["Cache-Control"]
    first = data["results"][0]
    assert first["observed_on"] is None and first["latest_metrics"]["value_kind"] == "illustrative"
    assert get(f'/api/v1/{kind}/{first["id"]}/')[0] == 200
    assert get(f"/api/v1/{kind}/export/")[0] == 200
    if kind == "ads":
        assert first["product"]["shop"]["id"] == first["shop"]["id"]
        asset = first["primary_media"]
        assert asset["video_url"] is None and get(asset["path"])[0] == 200
    print(f"PASS same-origin {kind}: {count} demo records, detail, export, provenance")

for path in ("/api/v1/filter-options/", "/api/v1/home/", "/api/v1/demo/entry-options/", "/api/v1/reports/overview/?focus=shops&period_days=90"):
    assert get(path)[0] == 200
print("PASS filter options, Home, example ideas and report overview")
assert get("/api/v1/workspaces/")[0] == 403
assert get("/api/v1/auth/me/")[0] == 403
print("PASS anonymous access to private workspace/session data rejected")

status, _, content = get("/api/v1/schema/")
assert status == 200
schema = json.loads(content)
assert len(schema["paths"]) >= 30
assert any(parameter["name"] == "X-CSRFToken" for parameter in schema["paths"]["/api/v1/auth/login/"]["post"]["parameters"])
status, _, content = get("/api/v1/docs/")
assert status == 200
html = content.decode("utf-8")
assert "http://backend:" not in html, "Container-only addresses must not reach the browser"
assets = [path for path in re.findall(r'(?:href|src)="([^"]+)"', html) if "/api/v1/static/" in path]
assert assets, "API documentation assets should be local"
for asset in assets:
    assert get(urllib.parse.urlsplit(asset).path)[0] == 200, asset
print(f"PASS validated OpenAPI ({len(schema['paths'])} paths), CSRF documentation and local Swagger assets")

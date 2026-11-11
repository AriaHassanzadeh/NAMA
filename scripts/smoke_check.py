"""Smoke-test local Compose; optionally verify a real DB outage and persistence."""
import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent.parent
values = dict(line.split("=", 1) for line in (root / ".env").read_text(encoding="utf-8").splitlines() if line and not line.startswith("#") and "=" in line)
frontend = "http://127.0.0.1:" + values.get("FRONTEND_PORT", "3000")
backend = "http://127.0.0.1:" + values.get("BACKEND_PORT", "8000")

def compose(*args):
    return subprocess.run(["docker", "compose", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()

def request(url):
    try:
        response = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url, timeout=12)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()

def expect_health(origin, expected):
    code, headers, body = request(origin + "/api/v1/health/")
    assert code == expected, f"Unexpected HTTP status: {code}"
    value = "ok" if expected == 200 else "unavailable"
    assert json.loads(body) == {"status": value, "database": value}, "Unexpected health payload"
    assert "no-store" in headers.get("Cache-Control", ""), "Health was cacheable"
    print(f"PASS {origin}/api/v1/health/ -> {code}, sanitized JSON, no-store")

def wait_ready():
    deadline = time.monotonic() + 60
    while True:
        try:
            code, _, _ = request(backend + "/api/v1/health/")
            if code == 200:
                return
        except (OSError, urllib.error.URLError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("Backend did not recover within 60 seconds")
        time.sleep(1)

def migration_count():
    return compose("exec", "-T", "db", "psql", "-U", values["POSTGRES_USER"], "-d", values["POSTGRES_DB"], "-Atc", "SELECT count(*) FROM django_migrations")

parser = argparse.ArgumentParser()
parser.add_argument("--database-cycle", action="store_true", help="Temporarily stop only this project's DB, then restore it")
args = parser.parse_args()
for origin in (backend, frontend):
    expect_health(origin, 200)
code, _, body = request(frontend + "/")
assert code == 200 and b'lang="fa"' in body and b'dir="rtl"' in body
assert request(frontend + "/mark.svg")[0] == 200
print("PASS Next.js page: HTTP 200, Persian RTL HTML, local logo asset")
if args.database_cycle:
    before = migration_count()
    assert int(before) > 0, "Migrations were not persisted"
    try:
        compose("stop", "db")
        for origin in (backend, frontend):
            expect_health(origin, 503)
    finally:
        compose("up", "-d", "--wait", "db")
        wait_ready()
    for origin in (backend, frontend):
        expect_health(origin, 200)
    after = migration_count()
    assert before == after, "Migration records did not survive DB stop/start"
    print(f"PASS database recovery and persisted migration rows: {after}; volume retained")

"""Add this local database to the installed Windows pgAdmin without replacing servers."""
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
values = {}
for line in (root / ".env").read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.lstrip().startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

install = Path(os.environ.get("PGADMIN_INSTALL_DIR", r"C:\Program Files\PostgreSQL\18\pgAdmin 4"))
python = install / "python" / "python.exe"
setup = install / "web" / "setup.py"
child_env = os.environ.copy()
child_env["PATH"] = str(install.parent / "bin") + os.pathsep + str(install / "runtime") + os.pathsep + child_env.get("PATH", "")
child_env["PSYCOPG_IMPL"] = "python"
config = Path(os.environ["APPDATA"]) / "pgAdmin" / "pgadmin4.db"
if not (python.is_file() and setup.is_file() and config.is_file()):
    raise SystemExit("Installed desktop pgAdmin/config not found; set PGADMIN_INSTALL_DIR if needed.")

host, port, name = "127.0.0.1", int(values.get("DATABASE_PORT", "5433")), "NAMA Analyze (Docker local)"
with sqlite3.connect(config.as_uri() + "?mode=ro", uri=True) as connection:
    before = connection.execute("SELECT id, name, host, port FROM server").fetchall()
    users = connection.execute("SELECT email FROM user ORDER BY id").fetchall()
if len(users) != 1:
    raise SystemExit("Multiple pgAdmin users found; select the intended account before importing.")
matching = [row for row in before if row[1] == name]
if matching and (len(matching) != 1 or matching[0][2:] != (host, port)):
    raise SystemExit("A different pgAdmin connection already uses this name; preserved without changes.")

local = config.parent / "nama-analyze"
local.mkdir(exist_ok=True)
passfile = local / "database.pgpass"
def escape(value):
    return str(value).replace("\\", "\\\\").replace(":", r"\:")
fields = [host, port, values["POSTGRES_DB"], values["POSTGRES_USER"], values["POSTGRES_PASSWORD"]]
passfile.write_text(":".join(escape(value) for value in fields) + "\n", encoding="utf-8")
server = {
    "Name": name, "Group": "Servers", "Host": host, "Port": port,
    "MaintenanceDB": values["POSTGRES_DB"], "Username": values["POSTGRES_USER"],
    "ConnectionParameters": {"sslmode": "prefer", "connect_timeout": 5, "passfile": passfile.as_posix()},
    "Comment": "NAMA Analyze milestone 01 - local Docker PostgreSQL 17 only",
}
export = local / "servers.json"
export.write_text(json.dumps({"Servers": {"1": server}}, indent=2) + "\n", encoding="utf-8")
if not matching:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = local / f"pgadmin4-before-import-{stamp}.db"
    with sqlite3.connect(config.as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(backup) as target:
        source.backup(target)
    result = subprocess.run([str(python), str(setup), "load-servers", str(export), "--sqlite-path", str(config), "--user", users[0][0]], capture_output=True, text=True, env=child_env)
    if result.returncode:
        raise SystemExit("pgAdmin import failed; previous servers and a configuration backup were preserved.")
with sqlite3.connect(config.as_uri() + "?mode=ro", uri=True) as connection:
    after = connection.execute("SELECT id, name, host, port FROM server").fetchall()
assert all(row in after for row in before), "An existing server entry changed"
assert len([row for row in after if row[1] == name and row[2:] == (host, port)]) == 1
print(f"pgAdmin server registered: {name}, {host}:{port}; existing servers preserved.")
print("Credentials are in a dedicated AppData passfile, outside the repository. Refresh Servers in pgAdmin.")

# Verify the same connection path pgAdmin uses, without passing a password on the command line.
probe = "import psycopg; c=psycopg.connect(host='127.0.0.1',port=" + str(port) + ",dbname=" + repr(values["POSTGRES_DB"]) + ",user=" + repr(values["POSTGRES_USER"]) + ",passfile=" + repr(str(passfile)) + ",connect_timeout=5); cur=c.cursor(); cur.execute('SELECT current_database(), version()'); print('pgAdmin connection verified:', cur.fetchone()); c.close()"
subprocess.run([str(python), "-c", probe], check=True, env=child_env)

"""Build database documentation from the live migrated PostgreSQL schema."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent
process = subprocess.run(["docker", "compose", "exec", "-T", "backend", "python", "manage.py", "export_database_schema"], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
schema = json.loads(process.stdout)
assert schema["engine"] == "postgresql"
tables = {table["name"]: table for table in schema["tables"]}
output = root / "docs" / "database"
output.mkdir(parents=True, exist_ok=True)
(output / "schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

groups = {
    "catalog": ["market_category", "market_country", "market_mediaasset", "market_shop", "market_product", "market_ad", "market_tag", "market_ad_tags", "market_shopmedia"],
    "metrics": ["market_shopmetrics", "market_productmetrics", "market_admetrics"],
    "workspaces": ["accounts_user", "accounts_emailverification", "workspaces_workspace", "workspaces_projectbrief", "workspaces_savedad", "workspaces_savedproduct", "workspaces_savedshop", "workspaces_shopwatch", "workspaces_savedreport"],
}

def node_id(name):
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])

def diagram(names):
    complete = set(names)
    related = {ref["table"] for name in names for column in tables[name]["columns"] for ref in column["references"]}
    names = list(names) + sorted(related - complete)
    lines = ["erDiagram", "    direction LR"]
    for name in names:
        assert name in tables, f"Missing actual table: {name}"
        lines.append(f'    {node_id(name)}["{name}"] {{')
        for column in tables[name]["columns"]:
            if name not in complete and "PK" not in column["keys"]:
                continue
            keys = " " + ", ".join(column["keys"]) if column["keys"] else ""
            notes = []
            if column["nullable"]:
                notes.append("nullable")
            if column["length"]:
                notes.append("max " + str(column["length"]))
            comment = ' "' + "; ".join(notes) + '"' if notes else ""
            lines.append(f'        {column["type"]} {column["name"]}{keys}{comment}')
        lines.append("    }")
    for name in sorted(complete):
        for column in tables[name]["columns"]:
            for ref in column["references"]:
                parent = "|o" if column["nullable"] else "||"
                child = "o|" if "UK" in column["keys"] or "PK" in column["keys"] else "o{"
                line = ".." if column["nullable"] else "--"
                lines.append(f'    {node_id(ref["table"])} {parent}{line}{child} {node_id(name)} : "{column["name"]}"')
    return "\n".join(lines) + "\n"

markdown = ["# Actual database schema", "", "Generated from the migrated local PostgreSQL database; no business rows or credentials are exported.", "", "The diagrams show physical tables, columns, keys and nullable foreign keys. External-context tables appear with their primary key only; their full columns are listed below.", "", "Demo data: 6 shops, 8 products, 10 ads and 9 image assets. Ad shop ownership is derived through Product, preventing mismatched Ad/Product/Shop references. Metrics are snapshots; reported counts are separate from actual demo-record counts. Currency is USD. Unknown observation dates are null; trends are undated ordinal indices.", "", "Workspace ownership protects briefs, bookmarks, watches and report definitions. accounts_user.password stores Django password hashes. Django's additional auth/session/admin tables are framework-managed.", ""]
for title, names in groups.items():
    source = diagram(names)
    (output / (title + ".mmd")).write_text(source, encoding="utf-8")
    markdown.extend(["## " + title.title(), "", "```mermaid", source.rstrip(), "```", ""])
markdown.extend(["## All application columns and database constraints", "", "Composite UNIQUE constraints appear under each table; individual columns are marked UK only when individually unique.", ""])
for table in schema["tables"]:
    if not table["name"].startswith(("market_", "workspaces_", "accounts_")):
        continue
    markdown.extend(["### " + table["name"], "", "| Column | PostgreSQL type | Nullable | Keys | References |", "| --- | --- | --- | --- | --- |"])
    for column in table["columns"]:
        sql_type = column["type"] + (f'({column["length"]})' if column["length"] else "")
        references = ", ".join(ref["table"] + "." + ref["column"] for ref in column["references"])
        markdown.append(f'| {column["name"]} | {sql_type} | {"yes" if column["nullable"] else "no"} | {", ".join(column["keys"])} | {references} |')
    markdown.extend(["", "```sql", *[item["name"] + ": " + item["definition"] for item in table["constraints"]], "```", ""])
markdown.extend(["## Regenerate", "", "```powershell", "python scripts/export_database_schema.py", "```", "", "Complete framework metadata is included in [database/schema.json](database/schema.json). These files describe the actual migrated schema; no external database service is involved.", ""])
(root / "docs" / "DATABASE.md").write_text("\n".join(markdown), encoding="utf-8")
print(f'Exported {len(tables)} actual PostgreSQL tables and three relationship diagrams to docs/DATABASE.md')

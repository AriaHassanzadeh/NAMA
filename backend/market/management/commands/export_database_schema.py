"""Export actual PostgreSQL columns/constraints, without selecting any row data."""
import json

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Export the migrated PostgreSQL schema as metadata-only JSON."

    def handle(self, *args, **options):
        result = {"engine": connection.vendor, "generated_at": timezone.now().isoformat(), "tables": []}
        with connection.cursor() as cursor:
            for table in sorted(connection.introspection.table_names(cursor)):
                constraints = connection.introspection.get_constraints(cursor, table)
                cursor.execute("""
                    SELECT column_name, udt_name, is_nullable, column_default,
                           character_maximum_length, numeric_precision, numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = current_schema() AND table_name = %s
                    ORDER BY ordinal_position
                """, [table])
                columns = []
                for name, sql_type, nullable, default, length, precision, scale in cursor.fetchall():
                    keys = []
                    references = []
                    for constraint in constraints.values():
                        if name not in constraint.get("columns", []):
                            continue
                        if constraint.get("primary_key"):
                            keys.append("PK")
                        elif constraint.get("unique") and len(constraint["columns"]) == 1:
                            keys.append("UK")
                        if constraint.get("foreign_key"):
                            keys.append("FK")
                            references.append({"table": constraint["foreign_key"][0], "column": constraint["foreign_key"][1]})
                    columns.append({"name": name, "type": sql_type, "nullable": nullable == "YES", "default": default,
                                    "length": length, "precision": precision, "scale": scale,
                                    "keys": sorted(set(keys), key=lambda key: ["PK", "FK", "UK"].index(key)), "references": references})
                cursor.execute("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = to_regclass(%s) ORDER BY conname", [table])
                result["tables"].append({"name": table, "columns": columns, "constraints": [{"name": name, "definition": definition} for name, definition in cursor.fetchall()]})
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))

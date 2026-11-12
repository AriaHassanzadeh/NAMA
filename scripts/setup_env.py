"""Generate local credentials once without printing or replacing secrets."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
target = root / ".env"
if target.exists():
    print(".env already exists; preserved without changes.")
else:
    template = (root / ".env.example").read_text(encoding="utf-8")
    content = template.replace("CHANGE_ME_DJANGO_SECRET", secrets.token_urlsafe(48))
    content = content.replace("CHANGE_ME_DATABASE_PASSWORD", secrets.token_urlsafe(32))
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print("Created ignored local .env; credentials were not printed.")

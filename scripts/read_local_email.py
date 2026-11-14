"""Open a local verification email; machine-readable links require explicit --json."""
import argparse
import json
import re
import webbrowser
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
from urllib.parse import urlsplit

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--recipient", required=True, help="Exact signup email address")
action = parser.add_mutually_exclusive_group()
action.add_argument("--open", action="store_true", help="Open the latest verification link in your browser")
action.add_argument("--json", action="store_true", help="Return the private link as JSON for local automated checks")
args = parser.parse_args()
values = {}
env_file = root / ".env"
if env_file.exists():
    values = dict(line.split("=", 1) for line in env_file.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#") and "=" in line)
origin = values.get("ACCOUNT_VERIFICATION_ORIGIN", "http://localhost:3000").rstrip("/")
recipient = args.recipient.strip().lower()
mailbox = root / "backend" / ".local-emails"
files = sorted(mailbox.glob("*.log"), key=lambda item: item.stat().st_mtime, reverse=True)
for file in files:
    message = BytesParser(policy=policy.default).parsebytes(file.read_bytes())
    if recipient not in {address.lower() for _, address in getaddresses(message.get_all("To", []))}:
        continue
    body = message.get_body(preferencelist=("plain",))
    text = body.get_content() if body else ""
    for url in re.findall(r"https?://[^\s<>]+/auth/verify#token=[A-Za-z0-9_-]+", text):
        parsed = urlsplit(url)
        if parsed.scheme + "://" + parsed.netloc != origin or parsed.path != "/auth/verify":
            continue
        if args.json:
            print(json.dumps({"verification_url": url, "subject": str(message.get("Subject", ""))}))
        elif args.open:
            webbrowser.open(url)
            print("Opened the latest local verification link in your browser.")
        else:
            print("A local verification email is available. Add --open to open its private link.")
        raise SystemExit(0)
raise SystemExit("No matching local verification email found. Complete signup or request another email first.")

"""Read isolated KT114 QA API pages for the view-equivalence test; no writes."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

root = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--database", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if not re.fullmatch(r"kt_readiness_[a-z0-9_]{1,40}", args.database):
    parser.error("Only an existing isolated kt_readiness_ QA database is allowed")
out = args.output.resolve()
if out == root or root in out.parents:
    parser.error("Keep fixture payload outside Git")
os.environ.update(
    POSTGRES_DB=args.database,
    POSTGRES_USER="kt_dev",
    POSTGRES_PASSWORD=os.environ["KT_READINESS_PASSWORD"],
    POSTGRES_HOST="127.0.0.1",
    POSTGRES_PORT="62224",
    DJANGO_SETTINGS_MODULE="config.settings",
    DJANGO_SECRET_KEY="kt118-readonly-fixture",
)
sys.path.insert(0, str(root / "apps/backend"))
import django
from django.conf import settings

settings.DATABASES["default"]["OPTIONS"]["options"] = (
    "-c default_transaction_read_only=on"
)
django.setup()
from catalog.api import list_items
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder

owner = get_user_model().objects.get(username="kt114-fixture")
pages, offset = [], 0
while True:
    data = list_items(SimpleNamespace(user=owner), limit=50, offset=offset)
    pages.append(data["results"])
    if data["next_offset"] is None:
        break
    offset = data["next_offset"]
out.write_text(
    json.dumps(
        {
            "source": "read-only PostgreSQL API service pages from KT114 synthetic corpus",
            "pages": pages,
        },
        cls=DjangoJSONEncoder,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(
    json.dumps(
        {"pages": len(pages), "items": sum(len(p) for p in pages), "read_only": True}
    )
)

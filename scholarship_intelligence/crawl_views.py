"""Dated, read-only dashboard views. The October baseline is never overwritten."""

from datetime import datetime, timezone, timedelta
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
from uuid import uuid4

from scholarship_intelligence.settings import PROJECT_ROOT

IST = timezone(timedelta(hours=5, minutes=30))
BASELINE = "2026-10-15"


def available(project_root=PROJECT_ROOT):
    root = Path(project_root)
    choices = [(BASELINE, "15 Oct 2026 · Original saved results")]
    directory = root / "data/runtime/crawl-views"
    for file in sorted(directory.glob("*.json.gz"), reverse=True) if directory.exists() else []:
        try:
            moment = datetime.strptime(file.name, "%Y%m%dT%H%M%S%f.json.gz")
            choices.append((file.name, moment.strftime("%d %b %Y · %I:%M:%S %p IST")))
        except ValueError:
            continue
    return choices


def load(selection=BASELINE, *, project_root=PROJECT_ROOT):
    root = Path(project_root).resolve()
    if selection == BASELINE:
        from scholarship_intelligence import preview
        manifest = json.loads((root / "data/samples/saved-results.manifest.json").read_bytes())
        payload = (root / "data/samples/saved-view.json.gz").read_bytes()
        if sha256(payload).hexdigest() != manifest["preview_sha256"]:
            raise ValueError("Original saved results failed the integrity check.")
        return json.loads(gzip.decompress(payload))["records"]
    if Path(selection).name != selection or selection not in {key for key, _ in available(root)}:
        raise ValueError("Unknown crawl selection.")
    payload = (root / "data/runtime/crawl-views" / selection).read_bytes()
    return json.loads(gzip.decompress(payload))["records"]


def save(records, *, project_root=PROJECT_ROOT, when=None):
    root = Path(project_root).resolve()
    directory = root / "data/runtime/crawl-views"
    directory.mkdir(parents=True, exist_ok=True)
    at = (when or datetime.now(timezone.utc)).astimezone(IST)
    filename = at.strftime("%Y%m%dT%H%M%S%f") + ".json.gz"
    destination = directory / filename
    temporary = directory / ("." + uuid4().hex + ".tmp")
    try:
        temporary.write_bytes(gzip.compress(json.dumps({"records": records}, ensure_ascii=False, allow_nan=False).encode(), compresslevel=6))
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return filename

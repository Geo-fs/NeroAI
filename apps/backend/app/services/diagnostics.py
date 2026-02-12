"""Diagnostics bundle export (sanitized)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
import uuid

from app.db.sqlite import DATA_DIR, connection
from app.services.audit import list_audit_logs
from app.services.settings_profiles import list_profiles, get_profile
from app.services.run_logger import list_runs


def export_diagnostics() -> str:
    bundle_id = f"diagnostics-{uuid.uuid4()}.zip"
    out_path = DATA_DIR / bundle_id
    runs = list_runs(limit=50)
    profiles = [get_profile(p["id"]) for p in list_profiles()]
    profiles_clean = []
    for p in profiles:
        if not p:
            continue
        payload = dict(p.get("payload", {}))
        payload.pop("policy_rules", None)
        profiles_clean.append({"id": p["id"], "name": p["name"], "payload": payload})
    logs = list_audit_logs(limit=200)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("audit_logs.json", json.dumps(logs, indent=2))
        zf.writestr("profiles.json", json.dumps(profiles_clean, indent=2))
        zf.writestr("runs.json", json.dumps(runs, indent=2))
        zf.writestr("environment.json", json.dumps({"data_dir": str(DATA_DIR)}, indent=2))
    return str(out_path)

"""SQLite helpers and schema migrations for backend persistence."""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "neroai.db"
DATA_DIR = DB_PATH.parent


def connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS model_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                is_local INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS permission_grants (
                id TEXT PRIMARY KEY,
                permission TEXT NOT NULL,
                scope TEXT NOT NULL,
                session_id TEXT,
                allowed_paths_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                definition_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                event_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                mode TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                input_text TEXT,
                model_source_id TEXT,
                model_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                duration_ms INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS run_events (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS memory_items (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS plugin_registry (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                path TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS vector_index (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                path TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                default_profile_id TEXT,
                default_model_source_id TEXT,
                default_model TEXT,
                logging_strictness TEXT NOT NULL DEFAULT 'standard',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS workspace_scopes (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                path TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            );

            CREATE TABLE IF NOT EXISTS workspace_tools (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            );

            CREATE TABLE IF NOT EXISTS workspace_settings (
                workspace_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                PRIMARY KEY (workspace_id, key),
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            );

            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_default INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS profile_settings (
                profile_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                PRIMARY KEY (profile_id, key),
                FOREIGN KEY(profile_id) REFERENCES profiles(id)
            );

            CREATE TABLE IF NOT EXISTS profile_history (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(profile_id) REFERENCES profiles(id)
            );

            CREATE TABLE IF NOT EXISTS settings_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 0,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings_profile_versions (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(profile_id) REFERENCES settings_profiles(id)
            );

            CREATE TABLE IF NOT EXISTS secrets (
                id TEXT PRIMARY KEY,
                key_name TEXT UNIQUE NOT NULL,
                encrypted_value TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.execute("DROP TABLE IF EXISTS ui_layouts")

        # Migrate legacy settings_profiles -> profiles/profile_settings (best-effort).
        cols = conn.execute("PRAGMA table_info(profiles)").fetchall()
        col_names = {row[1] for row in cols}
        if "version" not in col_names:
            conn.execute("ALTER TABLE profiles ADD COLUMN version INTEGER NOT NULL DEFAULT 1")

        legacy = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings_profiles'"
        ).fetchone()
        if legacy:
            rows = conn.execute(
                "SELECT id, name, payload_json, is_active FROM settings_profiles"
            ).fetchall()
            for row in rows:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO profiles (id, name, version, is_default, is_active)
                    VALUES (?, ?, 1, 0, ?)
                    """,
                    (row["id"], row["name"], row["is_active"]),
                )
                try:
                    payload = json.loads(row["payload_json"])
                except Exception:
                    payload = {}
                for key, value in payload.items():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO profile_settings (profile_id, key, value_json)
                        VALUES (?, ?, ?)
                        """,
                        (row["id"], key, json.dumps(value)),
                    )

        # Legacy column cleanup compatibility: old DBs may still have auth_token.
        cols = conn.execute("PRAGMA table_info(model_sources)").fetchall()
        col_names = {row[1] for row in cols}
        if "auth_token" in col_names:
            # Kept for backward compatibility read-path; we no longer write to it.
            pass

"""Initial data seeding for sources, settings, and default workflows."""

from __future__ import annotations

import json
import uuid

from app.db.sqlite import connection
from app.services.settings_service import DEFAULTS


def seed_defaults() -> None:
    with connection() as conn:
        local = conn.execute("SELECT id FROM model_sources WHERE is_local = 1").fetchone()
        if not local:
            conn.execute(
                "INSERT INTO model_sources (id, name, base_url, is_local) VALUES (?, ?, ?, 1)",
                ("local-ollama", "Local Ollama", "http://localhost:11434"),
            )

        for key, value in DEFAULTS.items():
            conn.execute(
                """
                INSERT INTO app_settings (key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO NOTHING
                """,
                (key, json.dumps(value)),
            )

        # Ensure a default profile exists for UI profile manager.
        profile_count = conn.execute("SELECT COUNT(1) AS c FROM profiles").fetchone()["c"]
        if profile_count == 0:
            profile_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO profiles (id, name, version, is_default, is_active)
                VALUES (?, ?, 1, 1, 1)
                """,
                (profile_id, "Default"),
            )
            for key, value in DEFAULTS.items():
                conn.execute(
                    "INSERT INTO profile_settings (profile_id, key, value_json) VALUES (?, ?, ?)",
                    (profile_id, key, json.dumps(value)),
                )
            conn.execute(
                "INSERT INTO profile_history (id, profile_id, snapshot_json) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), profile_id, json.dumps(DEFAULTS)),
            )

        wf_count = conn.execute("SELECT COUNT(1) AS c FROM workflows").fetchone()["c"]
        if wf_count == 0:
            summarize_folder = {
                "steps": [
                    {
                        "id": "list_files",
                        "type": "call_tool",
                        "tool_name": "file_list",
                        "input_template": {"path": "{{inputs.folder_path}}", "max_files": 20},
                    },
                    {
                        "id": "read_batch",
                        "type": "call_tool",
                        "tool_name": "file_read_batch",
                        "input_template": {"paths": "{{vars.list_files.files}}", "max_chars_per_file": 4000},
                    },
                    {
                        "id": "summary",
                        "type": "prompt_agent",
                        "prompt_template": "Summarize this folder content and provide key themes:\n{{vars.read_batch}}",
                    },
                    {"id": "done", "type": "return", "value_template": "{{vars.summary.output}}"},
                ]
            }
            search_then_answer = {
                "steps": [
                    {
                        "id": "search",
                        "type": "call_tool",
                        "tool_name": "web_search",
                        "input_template": {"query": "{{inputs.query}}", "num_results": 5, "safe": True},
                    },
                    {
                        "id": "has_results",
                        "type": "if",
                        "condition": "vars.search['status'] == 'ok'",
                        "then_steps": [
                            {
                                "id": "answer",
                                "type": "prompt_agent",
                                "prompt_template": "Answer using these sources with citations title+url:\n{{vars.search.results}}",
                            }
                        ],
                        "else_steps": [
                            {
                                "id": "answer_manual",
                                "type": "set_var",
                                "name": "answer",
                                "value": {"output": "Manual search input required. Please submit manual search results."},
                            }
                        ],
                    },
                    {"id": "done", "type": "return", "value_template": "{{vars.answer.output}}"},
                ]
            }
            for name, description, definition in [
                ("Summarize a folder", "Lists and reads text files in a folder then summarizes.", summarize_folder),
                ("Search then answer", "Runs web search and generates an answer with citations.", search_then_answer),
                (
                    "Explain run report generation",
                    "Explains how to read a run report and what it contains.",
                    {
                        "steps": [
                            {
                                "id": "explain",
                                "type": "prompt_agent",
                                "prompt_template": "Explain a run report: tools used, permissions, sources, and timings. Provide a short checklist.",
                            },
                            {"id": "done", "type": "return", "value_template": "{{vars.explain.output}}"},
                        ]
                    },
                ),
            ]:
                conn.execute(
                    "INSERT INTO workflows (id, name, description, definition_json) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), name, description, json.dumps(definition)),
                )

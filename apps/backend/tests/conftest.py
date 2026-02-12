from app.db.sqlite import initialize_db, connection


def pytest_runtest_setup() -> None:
    initialize_db()
    with connection() as conn:
        conn.execute("DELETE FROM permission_grants")
        conn.execute("DELETE FROM audit_logs")
        conn.execute("DELETE FROM secrets")
        conn.execute("DELETE FROM workspaces")
        conn.execute("DELETE FROM workspace_scopes")
        conn.execute("DELETE FROM workspace_tools")
        conn.execute("DELETE FROM workspace_settings")
        conn.execute("DELETE FROM profiles")
        conn.execute("DELETE FROM profile_settings")
        conn.execute("DELETE FROM profile_history")
        conn.execute("DELETE FROM app_settings")
        conn.execute("DELETE FROM runs")
        conn.execute("DELETE FROM run_events")
        conn.execute("DELETE FROM artifacts")
        conn.execute("DELETE FROM memory_items")
        conn.execute("DELETE FROM plugin_registry")
        conn.execute("DELETE FROM vector_index")

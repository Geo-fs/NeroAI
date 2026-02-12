from app.services.artifacts import create_artifact, delete_artifact, list_artifacts


def test_artifacts_crud() -> None:
    item = create_artifact(name="Report", content="hello", artifact_type="report", run_id=None, metadata={})
    assert item["name"] == "Report"
    items = list_artifacts()
    assert any(x["id"] == item["id"] for x in items)
    delete_artifact(item["id"])

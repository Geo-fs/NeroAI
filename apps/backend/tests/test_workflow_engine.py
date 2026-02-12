import pytest

from app.models.schemas import WorkflowResponse
from app.services.workflow_engine import run_workflow


@pytest.mark.anyio
async def test_workflow_if_else_branching() -> None:
    workflow = WorkflowResponse(
        id="w1",
        name="if-test",
        description="test",
        definition={
            "steps": [
                {"id": "init", "type": "set_var", "name": "flag", "value": "{{inputs.flag}}"},
                {
                    "id": "cond",
                    "type": "if",
                    "condition": "vars.flag == True",
                    "then_steps": [{"id": "then", "type": "set_var", "name": "answer", "value": "yes"}],
                    "else_steps": [{"id": "else", "type": "set_var", "name": "answer", "value": "no"}],
                },
                {"id": "ret", "type": "return", "value_template": "{{vars.answer}}"},
            ]
        },
    )
    out_true = await run_workflow(workflow, {"flag": True}, session_id="s1")
    out_false = await run_workflow(workflow, {"flag": False}, session_id="s1")
    assert out_true["return"] == "yes"
    assert out_false["return"] == "no"


@pytest.mark.anyio
async def test_workflow_loop() -> None:
    workflow = WorkflowResponse(
        id="w2",
        name="loop-test",
        description="test",
        definition={
            "steps": [
                {"id": "init", "type": "set_var", "name": "flag", "value": True},
                {
                    "id": "loop",
                    "type": "loop",
                    "condition": "vars.flag == True",
                    "max_iterations": 5,
                    "steps": [
                        {"id": "stop", "type": "set_var", "name": "flag", "value": False},
                    ],
                },
                {"id": "ret", "type": "return", "value_template": "{{vars.flag}}"},
            ]
        },
    )
    out = await run_workflow(workflow, {}, session_id="s1")
    assert out["return"] is not None

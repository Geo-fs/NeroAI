from app.services.policy_dsl import apply_limit_overrides, evaluate_effect, parse_policy


def test_policy_parse_and_effects() -> None:
    text = """
    deny(tool.file_write) always
    allow(web.search) only in profile=Research
    deny(process.run) unless confirm
    """
    parsed = parse_policy(text)
    assert parsed.errors == []
    assert evaluate_effect(parsed.effects, "tool.file_write", profile="Any", workspace=None) == "deny"
    assert evaluate_effect(parsed.effects, "web.search", profile="Research", workspace=None) == "allow"
    assert evaluate_effect(parsed.effects, "web.search", profile="Default", workspace=None) is None


def test_policy_limit_override() -> None:
    text = "max_tool_calls_per_message = 2 in profile=LockedDown"
    parsed = parse_policy(text)
    base = {"max_tool_calls_per_message": 5}
    updated = apply_limit_overrides(base, parsed.limits, profile="LockedDown", workspace=None)
    assert updated["max_tool_calls_per_message"] == 2

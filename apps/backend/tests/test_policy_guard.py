from app.services.policy_guard import policy_allows_action
from app.services.settings_profiles import activate_profile, create_profile


def test_policy_guard_denies_when_rule_matches() -> None:
    prof = create_profile("GuardTest", {"policy_rules": "deny(tool.file_write) always"})
    activate_profile(prof["id"])
    allowed, reason = policy_allows_action("tool.file_write")
    assert allowed is False
    assert "Policy denied" in reason

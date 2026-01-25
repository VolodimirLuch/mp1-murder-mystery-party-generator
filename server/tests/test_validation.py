from app.generator import validate_only


def test_validation_catches_missing_fields():
    invalid = {
        "character_packets": [],
        "solution": {"murderer_id": "char_01"},
        "timeline": [],
        "clues": [],
    }
    issues = validate_only(invalid)
    assert any("character_packets" in issue for issue in issues)
    assert any("timeline" in issue for issue in issues)
    assert any("clues" in issue for issue in issues)

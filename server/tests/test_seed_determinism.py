import os

from fastapi.testclient import TestClient

from app.main import app


def test_seed_determinism():
    os.environ["USE_MOCK_LLM"] = "1"
    client = TestClient(app)

    payload = {
        "player_count": 5,
        "category_id": "random",
        "tone": "suspense",
        "duration": 60,
        "seed": 424242,
    }
    first = client.post("/api/generate", json=payload)
    second = client.post("/api/generate", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200

    data_a = first.json()
    data_b = second.json()

    char_ids_a = [c["character_id"] for c in data_a["character_packets"]]
    char_ids_b = [c["character_id"] for c in data_b["character_packets"]]
    assert char_ids_a == char_ids_b

    clue_ids_a = [c["clue_id"] for c in data_a["clues"]]
    clue_ids_b = [c["clue_id"] for c in data_b["clues"]]
    assert clue_ids_a == clue_ids_b

    clue_assign_a = {c["character_id"]: c["clue_ids"] for c in data_a["character_packets"]}
    clue_assign_b = {c["character_id"]: c["clue_ids"] for c in data_b["character_packets"]}
    assert clue_assign_a == clue_assign_b

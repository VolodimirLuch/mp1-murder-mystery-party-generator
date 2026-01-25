import json

from app import generator
from app.models import GamePackage, GenerateRequest
from app.seed import seeded_random
from app.storage import get_categories


def test_normalization_coerces_types():
    request = GenerateRequest(
        player_count=4,
        category_id="random",
        tone="suspense",
        duration=60,
        seed=101,
    )
    categories = get_categories()
    rng = seeded_random(101)
    category = generator._select_category(categories, "random", rng)
    structure = generator._build_structure(request, category, 101, rng)

    candidate = {
        "character_packets": [
            {
                "character_id": structure["character_packets"][0]["character_id"],
                "intro_monologue": "Line one\nLine two",
                "traits": "curious; bold",
                "secrets": "- secret a\n- secret b",
            }
        ],
        "props_list": [
            {"name": "Name cards", "description": "Print on cardstock"},
            {"prop": "Clue envelopes"},
        ],
    }
    merged = generator._merge_structure(structure, candidate)
    normalized = generator._normalize_game_package(merged)

    packet = normalized["character_packets"][0]
    assert isinstance(packet["intro_monologue"], list)
    assert all(isinstance(item, str) for item in packet["intro_monologue"])
    assert isinstance(packet["traits"], list)
    assert isinstance(packet["secrets"], list)
    assert isinstance(normalized["props_list"], list)
    assert all(isinstance(item, str) for item in normalized["props_list"])

    GamePackage.model_validate(json.loads(json.dumps(normalized)))

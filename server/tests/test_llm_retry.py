import json
import os

from app import generator
from app.models import GenerateRequest
from app.seed import seeded_random
from app.storage import get_categories


class MockClient:
    def __init__(self, responses):
        self._responses = responses
        self.calls = 0

    def generate_text(self, **_kwargs):
        response = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        return response


def test_truncated_response_triggers_retry_and_repair(monkeypatch):
    os.environ["USE_MOCK_LLM"] = "0"

    request = GenerateRequest(
        player_count=4,
        category_id="random",
        tone="suspense",
        duration=60,
        seed=123,
    )
    categories = get_categories()
    rng = seeded_random(123)
    category = generator._select_category(categories, "random", rng)
    structure = generator._build_structure(request, category, 123, rng)
    valid_json = json.dumps(structure)

    responses = [
        '{"title":"Test","storyline_overview": [',
        '{"title":"Test" "theme_summary":"x"}',
        valid_json,
    ]
    mock_client = MockClient(responses)

    monkeypatch.setattr(generator, "TogetherClient", lambda: mock_client)
    monkeypatch.setattr(generator, "_validate_structure", lambda data, expected: [])

    result = generator.generate_game(request)
    assert mock_client.calls >= 3
    assert "title" in result

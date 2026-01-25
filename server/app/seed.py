from __future__ import annotations

import base64
import json
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional


MIN_PLAYERS = 4
MAX_PLAYERS = 20


@dataclass(frozen=True)
class ShareCodeData:
    seed: int
    player_count: int
    category_id: str
    tone: str
    duration: int


def normalize_seed(seed: Optional[int]) -> int:
    if seed is not None:
        return int(seed)
    return random.randint(100000, 999999999)


def seeded_random(seed: int) -> random.Random:
    rng = random.Random()
    rng.seed(seed)
    return rng


def encode_share_code(data: ShareCodeData) -> str:
    payload = {
        "seed": data.seed,
        "player_count": data.player_count,
        "category_id": data.category_id,
        "tone": data.tone,
        "duration": data.duration,
        "v": 1,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_share_code(code: str) -> ShareCodeData:
    padded = code + "=" * (-len(code) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
    payload: Dict[str, Any] = json.loads(raw)
    return ShareCodeData(
        seed=int(payload["seed"]),
        player_count=int(payload["player_count"]),
        category_id=str(payload["category_id"]),
        tone=str(payload["tone"]),
        duration=int(payload["duration"]),
    )


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}

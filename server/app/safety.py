from __future__ import annotations

from typing import List


DISALLOWED_KEYWORDS: List[str] = [
    "gore",
    "dismember",
    "suicide",
    "self-harm",
    "sexual",
    "rape",
    "racist",
    "hate crime",
]


def is_pg13(text: str) -> bool:
    lowered = text.lower()
    return not any(keyword in lowered for keyword in DISALLOWED_KEYWORDS)


def filter_or_raise(text: str) -> None:
    if not is_pg13(text):
        raise ValueError("Content failed PG-13 safety filter.")

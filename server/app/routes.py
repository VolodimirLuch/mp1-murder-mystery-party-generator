from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from .generator import generate_game, validate_only
from .models import Category, GenerateRequest
from .storage import get_categories


router = APIRouter()


@router.get("/api/categories", response_model=List[Category])
def list_categories() -> List[Category]:
    return get_categories()


@router.post("/api/generate", response_model=Dict[str, Any])
def generate(request: GenerateRequest) -> Dict[str, Any]:
    if request.player_names and len(request.player_names) != request.player_count:
        raise HTTPException(
            status_code=400,
            detail="player_names length must match player_count.",
        )
    try:
        return generate_game(request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/validate", response_model=Dict[str, Any])
def validate(payload: Dict[str, Any]) -> Dict[str, Any]:
    issues = validate_only(payload)
    return {"issues": issues}

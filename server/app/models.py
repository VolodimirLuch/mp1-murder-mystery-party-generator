from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Category(BaseModel):
    id: str
    name: str
    description: str
    tone_tags: List[str]
    suggested_props: List[str]
    suggested_archetypes: List[str]


class GenerateRequest(BaseModel):
    player_count: int = Field(..., ge=4, le=20)
    player_names: Optional[List[str]] = None
    category_id: str = Field(..., description="Category id or 'random'")
    tone: Optional[str] = Field(None, description="comedy/serious/suspense")
    duration: Optional[int] = Field(None, description="45/60/90")
    seed: Optional[int] = None


class Relationship(BaseModel):
    character_id: str
    relationship: str


class CharacterPacket(BaseModel):
    character_id: str
    name: str
    role_title: str
    backstory: str
    relationships: List[Relationship]
    connection_to_victim: str
    traits: List[str]
    public_goal: str
    secret_goal: str
    secrets: List[str]
    alibi: str
    clue_ids: List[str]
    intro_monologue: List[str]
    prop_suggestion: Optional[str] = None


class Victim(BaseModel):
    name: str
    role: str
    why_they_mattered: str


class Solution(BaseModel):
    murderer_id: str
    motive: str
    method: str
    opportunity: str
    reveal_explanation: str


class TimelineEvent(BaseModel):
    event_id: str
    time: str
    description: str


class Clue(BaseModel):
    clue_id: str
    title: str
    description: str
    type: str
    is_misleading: bool


class Round(BaseModel):
    round_id: str
    title: str
    description: str
    minutes: int


class GameMeta(BaseModel):
    seed: int
    share_code: str
    player_count: int
    category_id: str
    tone: str
    duration: int
    model: str


class GamePackage(BaseModel):
    title: str
    theme_summary: str
    storyline_overview: List[str]
    victim: Victim
    solution: Solution
    timeline: List[TimelineEvent]
    clues: List[Clue]
    character_packets: List[CharacterPacket]
    how_to_play: List[Round]
    props_list: List[str]
    meta: GameMeta

from __future__ import annotations

from pathlib import Path
from typing import List

from .models import Category


BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"


def get_categories() -> List[Category]:
    return [
        Category(
            id="gilded_gala",
            name="Gilded Age Gala",
            description="A lavish charity ball in a gilded mansion with old-money rivalries.",
            tone_tags=["opulent", "dramatic", "high-society"],
            suggested_props=["champagne flutes", "vintage invitations", "pocket watches"],
            suggested_archetypes=["heir", "socialite", "butler", "journalist"],
        ),
        Category(
            id="space_outpost",
            name="Deep Space Outpost",
            description="A remote research station orbiting a dying star.",
            tone_tags=["sci-fi", "claustrophobic", "suspense"],
            suggested_props=["mission patches", "flashlights", "oxygen gauges"],
            suggested_archetypes=["pilot", "scientist", "engineer", "medic"],
        ),
        Category(
            id="coastal_carnival",
            name="Coastal Carnival",
            description="A seaside carnival with odd attractions and rival families.",
            tone_tags=["whimsical", "mysterious", "nostalgic"],
            suggested_props=["ticket stubs", "carnival masks", "prize ribbons"],
            suggested_archetypes=["ringmaster", "fortune teller", "vendor", "detective"],
        ),
        Category(
            id="mountain_lodge",
            name="Snowed-In Mountain Lodge",
            description="A blizzard traps guests at a rustic lodge with a secret past.",
            tone_tags=["cozy", "tense", "isolated"],
            suggested_props=["scarves", "fireplace poker", "map of trails"],
            suggested_archetypes=["ranger", "celebrity", "chef", "writer"],
        ),
        Category(
            id="museum_heist",
            name="Museum After Hours",
            description="A private exhibit unveiling turns deadly in a grand museum.",
            tone_tags=["artful", "sleek", "intrigue"],
            suggested_props=["gallery badges", "gloves", "catalog pages"],
            suggested_archetypes=["curator", "collector", "security", "restorer"],
        ),
        Category(
            id="jazz_club",
            name="Midnight Jazz Club",
            description="A smoky jazz lounge where deals and melodies collide.",
            tone_tags=["noir", "stylish", "moody"],
            suggested_props=["sheet music", "matchbooks", "fedora"],
            suggested_archetypes=["musician", "club owner", "patron", "agent"],
        ),
        Category(
            id="fairytale_forest",
            name="Fairytale Forest Summit",
            description="Storybook figures negotiate a treaty in an enchanted glade.",
            tone_tags=["fantastical", "bright", "mischievous"],
            suggested_props=["crystal jars", "ribbons", "storybook pages"],
            suggested_archetypes=["prince", "witch", "ranger", "sprite"],
        ),
        Category(
            id="tech_retreat",
            name="Tech Founder Retreat",
            description="A startup retreat in a smart villa with hidden rivalries.",
            tone_tags=["modern", "competitive", "satirical"],
            suggested_props=["lanyards", "prototype gadgets", "whiteboard notes"],
            suggested_archetypes=["founder", "investor", "designer", "hacker"],
        ),
        Category(
            id="harbor_festival",
            name="Harbor Festival",
            description="A coastal town celebrates its maritime heritage.",
            tone_tags=["community", "warm", "stormy"],
            suggested_props=["rope knots", "ship logs", "festival pins"],
            suggested_archetypes=["captain", "mayor", "dockworker", "tourist"],
        ),
        Category(
            id="opera_premiere",
            name="Grand Opera Premiere",
            description="A famous premiere brings glamor, rivalries, and secrets.",
            tone_tags=["dramatic", "elegant", "high-stakes"],
            suggested_props=["playbills", "opera gloves", "tickets"],
            suggested_archetypes=["diva", "conductor", "patron", "stagehand"],
        ),
        Category(
            id="haunted_estate",
            name="Haunted Estate",
            description="A restored estate opens for a spooky fundraiser.",
            tone_tags=["spooky", "campy", "mystery"],
            suggested_props=["candles", "antique keys", "old photos"],
            suggested_archetypes=["historian", "medium", "caretaker", "guest"],
        ),
        Category(
            id="desert_rally",
            name="Desert Rally",
            description="A desert endurance rally with sponsors and rival teams.",
            tone_tags=["adventurous", "dusty", "competitive"],
            suggested_props=["race bibs", "goggles", "maps"],
            suggested_archetypes=["driver", "navigator", "mechanic", "journalist"],
        ),
    ]


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")

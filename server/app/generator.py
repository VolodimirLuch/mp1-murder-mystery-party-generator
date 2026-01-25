from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List

from .models import Category, GamePackage, GenerateRequest
from .safety import filter_or_raise
from .seed import MAX_PLAYERS, MIN_PLAYERS, ShareCodeData, encode_share_code, env_bool, normalize_seed, seeded_random
from .storage import get_categories, load_prompt
from .together_client import TogetherClient, TogetherClientError


DEFAULT_TONE = "suspense"
DEFAULT_DURATION = 60


FIRST_NAMES = [
    "Avery", "Blake", "Cameron", "Dakota", "Elliot", "Finley", "Harper",
    "Jordan", "Kai", "Logan", "Morgan", "Parker", "Quinn", "Reese", "Rowan",
    "Sawyer", "Skyler", "Taylor", "Zion", "Emerson",
]
LAST_NAMES = [
    "Hale", "Rowe", "Sterling", "Brooks", "Winslow", "Voss", "Kincaid",
    "Langford", "Maddox", "Sinclair", "Nolan", "Everett", "Pryce", "Monroe",
    "Blair", "Bennett", "Calloway", "Sutter", "Quincy", "Alden",
]


def _select_category(categories: List[Category], category_id: str, rng) -> Category:
    if category_id == "random":
        return rng.choice(categories)
    for cat in categories:
        if cat.id == category_id:
            return cat
    return categories[0]


def _generate_names(player_count: int, rng) -> List[str]:
    names: List[str] = []
    attempts = 0
    while len(names) < player_count and attempts < 200:
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if name not in names:
            names.append(name)
        attempts += 1
    return names


def _strip_json(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned).strip()
        cleaned = cleaned.rstrip("`").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        return cleaned[start : end + 1]
    return cleaned


def extract_json(text: str) -> str:
    cleaned = _strip_json(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found", cleaned, 0)
    return cleaned[start : end + 1]


def _is_balanced_json(text: str) -> bool:
    cleaned = _strip_json(text)
    brace = 0
    bracket = 0
    in_string = False
    escape = False
    for ch in cleaned:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            brace += 1
        elif ch == "}":
            brace -= 1
        elif ch == "[":
            bracket += 1
        elif ch == "]":
            bracket -= 1
    return brace == 0 and bracket == 0 and not in_string


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def parse_json_strict(text: str) -> Dict[str, Any]:
    cleaned = _strip_json(text)
    if not _is_balanced_json(cleaned):
        raise json.JSONDecodeError("Unbalanced JSON", cleaned, 0)
    extracted = extract_json(cleaned)
    try:
        return json.loads(extracted)
    except json.JSONDecodeError:
        repaired = _remove_trailing_commas(extracted)
        return json.loads(repaired)


def _split_text_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = re.split(r"(?:\r?\n|;|•)", value)
        cleaned = [part.strip(" \t-•") for part in parts if part.strip(" \t-•")]
        return cleaned or [value.strip()]
    return [str(value).strip()]


def _normalize_props_list(props: Any) -> List[str]:
    if props is None:
        return []
    if isinstance(props, dict):
        props = [props]
    if not isinstance(props, list):
        return [str(props)]
    normalized: List[str] = []
    for item in props:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            description = str(item.get("description", "")).strip()
            if name and description:
                normalized.append(f"{name}: {description}")
            elif name:
                normalized.append(name)
            elif description:
                normalized.append(description)
            else:
                normalized.append(", ".join(f"{k}: {v}" for k, v in item.items()))
        else:
            normalized.append(str(item))
    return [entry for entry in normalized if entry.strip()]


def _normalize_game_package(data: Dict[str, Any]) -> Dict[str, Any]:
    packets = data.get("character_packets", [])
    for packet in packets:
        intro = packet.get("intro_monologue")
        if isinstance(intro, str):
            lines = intro.splitlines() if "\n" in intro else [intro]
            packet["intro_monologue"] = [line.strip() for line in lines if line.strip()]
        else:
            packet["intro_monologue"] = _split_text_list(intro)

        for field in ("traits", "secrets"):
            value = packet.get(field)
            if isinstance(value, str):
                packet[field] = _split_text_list(value)
            else:
                packet[field] = _split_text_list(value)

    data["props_list"] = _normalize_props_list(data.get("props_list"))
    return data


def _log_llm_debug(response: str) -> None:
    if not env_bool("DEBUG_LLM_OUTPUT", False):
        return
    logger = logging.getLogger("mp1.llm")
    tail = response[-300:] if response else ""
    logger.info(
        "LLM response len=%s balanced=%s tail=%r",
        len(response),
        _is_balanced_json(response),
        tail,
    )


def repair_invalid_json(
    client: TogetherClient,
    system_prompt: str,
    raw_text: str,
    err_msg: str,
    structure_template: str,
    max_tokens: int,
) -> Dict[str, Any]:
    validation_prompt = load_prompt("validation_prompt.md")
    repair_prompt = validation_prompt.format(
        issues=f"- JSON parse error: {err_msg}",
        structure=structure_template,
        candidate=json.dumps({"raw_output": raw_text}, indent=2),
    )
    response = client.generate_text(
        prompt=repair_prompt,
        system_prompt=system_prompt,
        temperature=0.2,
        top_p=0.8,
        max_tokens=max_tokens,
    )
    _log_llm_debug(response)
    return parse_json_strict(response)


def _build_structure(
    request: GenerateRequest,
    category: Category,
    seed: int,
    rng,
) -> Dict[str, Any]:
    player_count = request.player_count
    character_ids = [f"char_{i+1:02d}" for i in range(player_count)]
    clue_count = max(12, player_count * 2)
    clue_ids = [f"clue_{i+1:02d}" for i in range(clue_count)]
    timeline_ids = [f"event_{i+1:02d}" for i in range(8)]
    round_ids = [f"round_{i+1:02d}" for i in range(4)]

    hard_count = max(3, int(clue_count * 0.25))
    hard_indices = set(rng.sample(range(clue_count), hard_count))
    misleading_count = max(1, int(clue_count * 0.3))
    misleading_indices = set(rng.sample(range(clue_count), misleading_count))

    clues = []
    for idx, clue_id in enumerate(clue_ids):
        clues.append(
            {
                "clue_id": clue_id,
                "title": "",
                "description": "",
                "type": "hard" if idx in hard_indices else "soft",
                "is_misleading": idx in misleading_indices,
            }
        )

    rng.shuffle(clue_ids)
    clue_assignments: Dict[str, List[str]] = {cid: [] for cid in character_ids}
    for i, clue_id in enumerate(clue_ids):
        clue_assignments[character_ids[i % player_count]].append(clue_id)
    for cid in character_ids:
        if len(clue_assignments[cid]) < 2:
            extra = rng.sample(clue_ids, 2 - len(clue_assignments[cid]))
            clue_assignments[cid].extend(extra)
        if len(clue_assignments[cid]) > 3:
            clue_assignments[cid] = clue_assignments[cid][:3]

    relationships = {}
    for i, cid in enumerate(character_ids):
        others = [
            character_ids[(i + 1) % player_count],
            character_ids[(i + 2) % player_count],
        ]
        if player_count > 4 and rng.random() > 0.5:
            others.append(character_ids[(i + 3) % player_count])
        relationships[cid] = [{"character_id": oid, "relationship": ""} for oid in others]

    murderer_id = rng.choice(character_ids)
    victim_name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"

    character_packets = []
    names = request.player_names or _generate_names(player_count, rng)
    for idx, cid in enumerate(character_ids):
        character_packets.append(
            {
                "character_id": cid,
                "name": names[idx],
                "role_title": "",
                "backstory": "",
                "relationships": relationships[cid],
                "connection_to_victim": "",
                "traits": [],
                "public_goal": "",
                "secret_goal": "",
                "secrets": [],
                "alibi": "",
                "clue_ids": clue_assignments[cid],
                "intro_monologue": [],
                "prop_suggestion": "",
            }
        )

    structure = {
        "title": "",
        "theme_summary": "",
        "storyline_overview": [],
        "victim": {
            "name": victim_name,
            "role": "",
            "why_they_mattered": "",
        },
        "solution": {
            "murderer_id": murderer_id,
            "motive": "",
            "method": "",
            "opportunity": "",
            "reveal_explanation": "",
        },
        "timeline": [{"event_id": eid, "time": "", "description": ""} for eid in timeline_ids],
        "clues": clues,
        "character_packets": character_packets,
        "how_to_play": [
            {"round_id": rid, "title": "", "description": "", "minutes": 0} for rid in round_ids
        ],
        "props_list": [],
        "meta": {
            "seed": seed,
            "share_code": "",
            "player_count": player_count,
            "category_id": category.id,
            "tone": request.tone or DEFAULT_TONE,
            "duration": request.duration or DEFAULT_DURATION,
            "model": "",
        },
    }
    return structure


def _validate_structure(data: Dict[str, Any], expected: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    player_count = expected["player_count"]
    character_ids = expected["character_ids"]
    clue_ids = expected["clue_ids"]

    packets = data.get("character_packets", [])
    if len(packets) != player_count:
        issues.append("player_count does not match character_packets length.")

    murderer_id = data.get("solution", {}).get("murderer_id")
    if murderer_id not in character_ids:
        issues.append("murderer_id is not one of the characters.")

    timeline = data.get("timeline", [])
    if len(timeline) < 8:
        issues.append("timeline has fewer than 8 events.")

    clues = data.get("clues", [])
    if len(clues) < 12:
        issues.append("clues has fewer than 12 items.")
    clue_id_set = {c.get("clue_id") for c in clues}
    if not set(clue_ids).issubset(clue_id_set):
        issues.append("clue ids missing from clues list.")
    hard_evidence = [c for c in clues if c.get("type") == "hard"]
    if len(hard_evidence) < 3:
        issues.append("hard evidence clues fewer than 3.")

    graph = {cid: set() for cid in character_ids}
    for packet in packets:
        rels = packet.get("relationships", [])
        if len(rels) < 2:
            issues.append(f"character {packet.get('character_id')} has too few relationships.")
        if not packet.get("connection_to_victim"):
            issues.append(f"character {packet.get('character_id')} missing connection_to_victim.")
        for rel in rels:
            target = rel.get("character_id")
            if target in graph:
                graph[packet.get("character_id")].add(target)
    if not _is_connected(graph):
        issues.append("relationship graph is not connected.")

    for packet in packets:
        if not packet.get("clue_ids"):
            issues.append(f"character {packet.get('character_id')} missing clue_ids.")
        else:
            for clue_id in packet.get("clue_ids", []):
                if clue_id not in clue_ids:
                    issues.append("character packet references unknown clue_id.")
                    break
    return issues


def _is_connected(graph: Dict[str, set]) -> bool:
    if not graph:
        return False
    start = next(iter(graph))
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        stack.extend(graph[node] - visited)
    return len(visited) == len(graph)


def _fill_mock(structure: Dict[str, Any], category: Category) -> Dict[str, Any]:
    structure["title"] = f"{category.name}: A Night of Secrets"
    structure["theme_summary"] = (
        f"A {category.tone_tags[0]} mystery set in {category.description.lower()}"
    )
    structure["storyline_overview"] = [
        "Guests arrive to a gathering that promises celebration.",
        "A sudden discovery shifts the mood and exposes hidden conflicts.",
        "As tension rises, alliances form and secrets surface.",
    ]
    structure["victim"]["role"] = "Beloved organizer"
    structure["victim"]["why_they_mattered"] = "They controlled access to a key legacy."
    structure["solution"]["motive"] = "A long-simmering betrayal over inheritance."
    structure["solution"]["method"] = "Poisoned toast at a private moment."
    structure["solution"]["opportunity"] = "The murderer had access to the victim's drink."
    structure["solution"]["reveal_explanation"] = "Clue patterns and alibis converge on the culprit."
    for event in structure["timeline"]:
        event["time"] = "20:00"
        event["description"] = "A notable event shifts the night."
    for clue in structure["clues"]:
        clue["title"] = "Suspicious detail"
        clue["description"] = "A detail that hints at motive or method."
    for packet in structure["character_packets"]:
        packet["role_title"] = "Guest with secrets"
        packet["backstory"] = "A brief history tied to the gathering."
        for rel in packet["relationships"]:
            rel["relationship"] = "old friend"
        packet["connection_to_victim"] = "Owed the victim a favor."
        packet["traits"] = ["calm", "observant"]
        packet["public_goal"] = "Keep the event running smoothly."
        packet["secret_goal"] = "Recover a missing document."
        packet["secrets"] = ["Once threatened the victim.", "Hiding a financial loss."]
        packet["alibi"] = "Was speaking with staff during the incident."
        packet["intro_monologue"] = [
            "I didn't expect this night to turn dark.",
            "We all have reasons to be here.",
        ]
        packet["prop_suggestion"] = "A distinctive accessory"
    for round_info in structure["how_to_play"]:
        round_info["title"] = "Investigation Round"
        round_info["description"] = "Players share clues and challenge alibis."
        round_info["minutes"] = 15
    structure["props_list"] = [
        "Name cards",
        "Evidence cards",
        "Clue envelopes",
        "Timeline board",
    ]
    return structure


def _merge_relationships(
    base: List[Dict[str, Any]], update: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    update_map = {rel.get("character_id"): rel for rel in update}
    merged = []
    for rel in base:
        updated = update_map.get(rel.get("character_id"), {})
        merged.append(
            {
                "character_id": rel.get("character_id"),
                "relationship": updated.get("relationship", rel.get("relationship", "")),
            }
        )
    return merged


def _merge_structure(structure: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    merged = structure

    for key, value in candidate.items():
        if key not in merged:
            continue

        if key == "character_packets" and isinstance(value, list):
            base_packets = {p["character_id"]: p for p in merged["character_packets"]}
            for packet in value:
                cid = packet.get("character_id")
                if cid not in base_packets:
                    continue
                base = base_packets[cid]
                base["role_title"] = packet.get("role_title", base["role_title"])
                base["backstory"] = packet.get("backstory", base["backstory"])
                base["relationships"] = _merge_relationships(
                    base.get("relationships", []), packet.get("relationships", [])
                )
                base["connection_to_victim"] = packet.get(
                    "connection_to_victim", base.get("connection_to_victim", "")
                )
                base["traits"] = packet.get("traits", base.get("traits", []))
                base["public_goal"] = packet.get("public_goal", base.get("public_goal", ""))
                base["secret_goal"] = packet.get("secret_goal", base.get("secret_goal", ""))
                base["secrets"] = packet.get("secrets", base.get("secrets", []))
                base["alibi"] = packet.get("alibi", base.get("alibi", ""))
                base["intro_monologue"] = packet.get(
                    "intro_monologue", base.get("intro_monologue", [])
                )
                base["prop_suggestion"] = packet.get(
                    "prop_suggestion", base.get("prop_suggestion", "")
                )
            merged["character_packets"] = list(base_packets.values())
            continue

        if key == "clues" and isinstance(value, list):
            base_clues = {c["clue_id"]: c for c in merged["clues"]}
            for clue in value:
                cid = clue.get("clue_id")
                if cid not in base_clues:
                    continue
                base = base_clues[cid]
                base["title"] = clue.get("title", base["title"])
                base["description"] = clue.get("description", base["description"])
            merged["clues"] = list(base_clues.values())
            continue

        if key == "timeline" and isinstance(value, list):
            base_events = {e["event_id"]: e for e in merged["timeline"]}
            for event in value:
                eid = event.get("event_id")
                if eid not in base_events:
                    continue
                base = base_events[eid]
                base["time"] = event.get("time", base["time"])
                base["description"] = event.get("description", base["description"])
            merged["timeline"] = list(base_events.values())
            continue

        if key == "how_to_play" and isinstance(value, list):
            base_rounds = {r["round_id"]: r for r in merged["how_to_play"]}
            for rnd in value:
                rid = rnd.get("round_id")
                if rid not in base_rounds:
                    continue
                base = base_rounds[rid]
                base["title"] = rnd.get("title", base["title"])
                base["description"] = rnd.get("description", base["description"])
                base["minutes"] = rnd.get("minutes", base["minutes"])
            merged["how_to_play"] = list(base_rounds.values())
            continue

        if isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value

    return merged


def generate_game(request: GenerateRequest) -> Dict[str, Any]:
    if request.player_count < MIN_PLAYERS or request.player_count > MAX_PLAYERS:
        raise ValueError("player_count out of range.")

    categories = get_categories()
    seed = normalize_seed(request.seed)
    rng = seeded_random(seed)
    category = _select_category(categories, request.category_id, rng)

    structure = _build_structure(request, category, seed, rng)
    share_data = ShareCodeData(
        seed=seed,
        player_count=request.player_count,
        category_id=category.id,
        tone=request.tone or DEFAULT_TONE,
        duration=request.duration or DEFAULT_DURATION,
    )
    share_code = encode_share_code(share_data)
    structure["meta"]["share_code"] = share_code
    structure["meta"]["model"] = os.getenv(
        "TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    )

    expected = {
        "player_count": request.player_count,
        "character_ids": [p["character_id"] for p in structure["character_packets"]],
        "clue_ids": [c["clue_id"] for c in structure["clues"]],
    }

    if env_bool("USE_MOCK_LLM", False):
        candidate = _fill_mock(structure, category)
        issues = _validate_structure(candidate, expected)
        if issues:
            raise ValueError(f"Mock generation failed validation: {issues}")
        GamePackage.model_validate(candidate)
        return candidate

    system_prompt = load_prompt("system_prompt.md")
    generation_template = load_prompt("game_generation_prompt.md")
    compact_structure = json.dumps(structure, separators=(",", ":"))
    base_tokens = 3200
    extra_tokens = max(0, request.player_count - 6) * 250
    max_tokens = min(6500, base_tokens + extra_tokens)
    retry_max_tokens = min(6500, max_tokens + 800)
    prompt = generation_template.format(
        category_name=category.name,
        category_description=category.description,
        tone_tags=", ".join(category.tone_tags),
        suggested_props=", ".join(category.suggested_props),
        suggested_archetypes=", ".join(category.suggested_archetypes),
        seed=seed,
        structure=compact_structure,
    )

    client = TogetherClient()
    try:
        response = client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            top_p=0.85,
            max_tokens=max_tokens,
        )
    except TogetherClientError as exc:
        raise RuntimeError(str(exc)) from exc
    _log_llm_debug(response)

    try:
        candidate = parse_json_strict(response)
    except json.JSONDecodeError as exc:
        if not _is_balanced_json(response):
            response = client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                top_p=0.85,
                max_tokens=retry_max_tokens,
            )
            _log_llm_debug(response)
            try:
                candidate = parse_json_strict(response)
            except json.JSONDecodeError as retry_exc:
                candidate = repair_invalid_json(
                    client,
                    system_prompt,
                    response,
                    str(retry_exc),
                    compact_structure,
                    retry_max_tokens,
                )
        else:
            candidate = repair_invalid_json(
                client,
                system_prompt,
                response,
                str(exc),
                compact_structure,
                max_tokens,
            )
    merged = _merge_structure(structure, candidate)
    merged = _normalize_game_package(merged)
    issues = _validate_structure(merged, expected)

    if issues:
        validation_prompt = load_prompt("validation_prompt.md")
        repair_prompt = validation_prompt.format(
            issues="\n".join(f"- {issue}" for issue in issues),
            structure=compact_structure,
            candidate=json.dumps(merged, indent=2),
        )
        response = client.generate_text(
            prompt=repair_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            top_p=0.85,
            max_tokens=retry_max_tokens,
        )
        _log_llm_debug(response)
        candidate = parse_json_strict(response)
        merged = _merge_structure(structure, candidate)
        merged = _normalize_game_package(merged)
        issues = _validate_structure(merged, expected)
        if issues:
            raise ValueError(f"Validation failed after repair: {issues}")

    filter_or_raise(json.dumps(merged))
    GamePackage.model_validate(merged)
    return merged


def validate_only(data: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    if "character_packets" not in data:
        issues.append("character_packets missing.")
    elif not isinstance(data.get("character_packets"), list) or not data.get("character_packets"):
        issues.append("character_packets empty or invalid.")
    if "solution" not in data:
        issues.append("solution missing.")
    if "timeline" not in data:
        issues.append("timeline missing.")
    elif not isinstance(data.get("timeline"), list) or not data.get("timeline"):
        issues.append("timeline empty or invalid.")
    if "clues" not in data:
        issues.append("clues missing.")
    elif not isinstance(data.get("clues"), list) or not data.get("clues"):
        issues.append("clues empty or invalid.")

    expected = {
        "player_count": len(data.get("character_packets", [])),
        "character_ids": [p.get("character_id") for p in data.get("character_packets", [])],
        "clue_ids": [c.get("clue_id") for c in data.get("clues", [])],
    }
    return issues + _validate_structure(data, expected)

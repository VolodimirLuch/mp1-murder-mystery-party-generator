# Project Manual

## MP1 -- Murder Mystery Party Generator

### Overview
This project is a full-stack murder mystery party kit generator. A browser client collects
player and theme options, a FastAPI server calls Together.ai to generate a complete
GamePackage JSON, and the client renders the results with player and host views. The
package includes storyline, victim, solution, timeline, clues, character packets, rounds,
and printable prop suggestions.

### Feature Summary
- Browser client with step-by-step inputs, results view, and localStorage persistence.
- FastAPI server with `/api/generate`, `/api/categories`, `/api/validate`, and `/health`.
- Deterministic structure using a seeded PRNG and share-code regeneration.
- LLM generation with strict JSON parsing, retry/repair prompts, and validation.
- Safety filter to enforce PG-13 content.
- Host access and solution reveal are guarded by browser confirm dialogs (no custom modal).

### Architecture (Detailed)
```
Browser UI (client/index.html + client/app.js)
   |
   |  fetch POST /api/generate
   |  payload: player_count, names?, category_id, tone, duration, seed
   v
FastAPI (server/app/main.py + server/app/routes.py)
   |
   |  generate_game()
   |    - build base structure + ids
   |    - TogetherClient -> Together.ai
   |    - parse_json_strict -> repair_invalid_json
   |    - merge template + candidate
   |    - validate + repair
   |    - response validation + safety filter
   v
GamePackage JSON
   |
   |  render results + host/player view
   |  save to localStorage
   v
Browser UI
```

### Data Flow Walkthrough (Generate)
1. User fills player count, optional names, category, tone, duration, seed.
2. Client sends `POST /api/generate`.
3. Server builds a deterministic structure with ids and assignments.
4. Server calls Together.ai with a strict JSON template prompt.
5. Response is parsed strictly; malformed JSON triggers retry/repair.
6. Template ids are merged with LLM content.
7. Validation enforces counts, ids, and connectivity; repair runs if needed.
8. PG-13 filter runs; Pydantic validates the final GamePackage.
9. Client renders results and stores the last game in localStorage.

### Repository Structure
```
mp1_murder_mystery/
  client/
    index.html
    styles.css
    app.js
  server/
    app/
      __init__.py
      main.py
      routes.py
      models.py
      generator.py
      together_client.py
      safety.py
      seed.py
      storage.py
    prompts/
      system_prompt.md
      game_generation_prompt.md
      validation_prompt.md
      README_PROMPTS.md
    tests/
      test_seed_determinism.py
      test_validation.py
      test_normalization.py
      test_llm_retry.py
    requirements.txt
    .env.example
  docs/
    PROJECT_MANUAL.md
    AI_COLLAB_NOTES.md
  README.md
```

### Server Module Responsibilities
- `server/app/main.py`: FastAPI app, `/health`, static file mount, and index route.
- `server/app/routes.py`: API endpoints for categories, generate, and validate.
- `server/app/models.py`: Pydantic models for request/response schemas.
- `server/app/generator.py`: generation pipeline, JSON parsing/repair, validation.
- `server/app/together_client.py`: Together.ai HTTP client.
- `server/app/safety.py`: PG-13 filter via keyword blocklist.
- `server/app/seed.py`: deterministic seed and share code encoding/decoding.
- `server/app/storage.py`: in-memory categories and prompt loader.

### Tests
- `test_seed_determinism.py`: same inputs + seed yield stable ids and assignments.
- `test_validation.py`: missing/empty fields are flagged by validation.
- `test_normalization.py`: coercion for list/string mismatches before Pydantic validation.
- `test_llm_retry.py`: truncated responses trigger retry/repair logic.

### Client Responsibilities
- `client/index.html`: step-by-step form layout, results, host/player sections.
- `client/app.js`: fetch calls, rendering, share code handling, localStorage.
- `client/styles.css`: noir/case-file theme and UI styling.

## API Documentation

### `GET /health`
- Response: `{ "ok": true }`

### `GET /api/categories`
- Response schema: `Category[]`
  - `id`, `name`, `description`, `tone_tags[]`, `suggested_props[]`, `suggested_archetypes[]`

Example response (trimmed):
```json
[
  {
    "id": "gilded_gala",
    "name": "Gilded Age Gala",
    "description": "A lavish charity ball in a gilded mansion with old-money rivalries.",
    "tone_tags": ["opulent", "dramatic", "high-society"],
    "suggested_props": ["champagne flutes", "vintage invitations", "pocket watches"],
    "suggested_archetypes": ["heir", "socialite", "butler", "journalist"]
  }
]
```

### `POST /api/generate`
- Request schema (`GenerateRequest`):
  - `player_count` (int, 4-20)
  - `player_names` (optional list[str])
  - `category_id` (string or `"random"`)
  - `tone` (optional string)
  - `duration` (optional int)
  - `seed` (optional int)

Example request:
```json
{
  "player_count": 6,
  "player_names": ["Avery", "Blake", "Cameron", "Dakota", "Elliot", "Finley"],
  "category_id": "jazz_club",
  "tone": "suspense",
  "duration": 60,
  "seed": 424242
}
```

Response schema (`GamePackage`):
- `title`, `theme_summary`, `storyline_overview[]`
- `victim`, `solution`, `timeline[]`, `clues[]`
- `character_packets[]`, `how_to_play[]`, `props_list[]`, `meta`

Example response (trimmed):
```json
{
  "title": "Midnight Jazz Club: A Night of Secrets",
  "theme_summary": "A noir mystery set in a smoky jazz lounge.",
  "storyline_overview": ["...", "..."],
  "victim": {"name": "Avery Hale", "role": "Club patron", "why_they_mattered": "..."},
  "solution": {
    "murderer_id": "char_03",
    "motive": "...",
    "method": "...",
    "opportunity": "...",
    "reveal_explanation": "..."
  },
  "timeline": [{"event_id": "event_01", "time": "19:30", "description": "..."}],
  "clues": [{"clue_id": "clue_01", "title": "...", "description": "...", "type": "hard", "is_misleading": false}],
  "character_packets": [{"character_id": "char_01", "name": "Blake Rowe", "role_title": "...", "clue_ids": ["clue_01"], "intro_monologue": ["..."]}],
  "how_to_play": [{"round_id": "round_01", "title": "Arrival", "description": "...", "minutes": 15}],
  "props_list": ["Name cards", "Evidence cards"],
  "meta": {
    "seed": 424242,
    "share_code": "eyJ...",
    "player_count": 6,
    "category_id": "jazz_club",
    "tone": "suspense",
    "duration": 60,
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
  }
}
```

Errors:
- `400`: `player_names` length mismatch.
- `500`: Together.ai failures, validation failures, or missing API key.

### `POST /api/validate`
- Request: any JSON payload
- Response: `{ "issues": [string] }`

## Generation Pipeline and Validation

### Base Structure and IDs
- `generator._build_structure()` creates:
  - `char_01..char_N` ids
  - `clue_01..` ids
  - `event_01..` timeline ids
  - `round_01..` round ids
- Assigns 2–3 clues per character deterministically.
- Chooses a murderer id from the character list.
- Builds a minimal relationships graph linking 2–4 neighbors.

### Categories
- `storage.get_categories()` returns the curated list.
- `category_id="random"` uses the seeded RNG to select.
- Each category includes tone tags, props, and archetypes.

### Clues and Evidence
- Hard evidence count: `max(3, 25% of clues)`.
- Misleading clues: ~30% of clues (flagged internally).

### JSON Parsing and Repair
- `parse_json_strict()`:
  - strips code fences,
  - checks balanced braces/brackets,
  - parses JSON,
  - removes trailing commas as a final attempt.
- If unbalanced/truncated, a retry is issued with higher `max_tokens`.
- `repair_invalid_json()` uses the validation prompt to force JSON-only output.
- No YAML fallback is used in the pipeline.

### Merging and Validation
- `_merge_structure()` keeps template ids authoritative and applies LLM text.
- `_validate_structure()` checks:
  - character count matches `player_count`
  - `murderer_id` is in character list
  - timeline length >= 8
  - clues >= 12 with >= 3 hard evidence
  - relationships graph is connected
  - clue references are valid
- `_normalize_game_package()` coerces list fields:
  - `intro_monologue` (string -> list)
  - `traits`/`secrets` (string -> list)
  - `props_list` (dict -> readable string list)
- `GamePackage.model_validate()` enforces schema compliance.

### Determinism + Share Codes
- `seed.py` provides deterministic PRNG for ids, assignments, and random selections.
- Share code encodes: `seed`, `player_count`, `category_id`, `tone`, `duration` (plus `v`).
- Deterministic portions: ids, clue assignment, category selection (if random).
- LLM text content is nondeterministic but is prompted with the seed.

## Environment Setup + Run Guide (Windows)

### Prerequisites
- Python 3.11+ recommended
- pip installed
- Together.ai API key

### Create and Use a Virtual Environment
```bash
cd mp1_murder_mystery/server
python -m venv .venv
```

Activate (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell scripts are blocked, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Install Dependencies
```bash
cd mp1_murder_mystery/server
pip install -r requirements.txt
```

### Environment Variables
- `TOGETHER_API_KEY` (required)
- `TOGETHER_MODEL` (optional, default in `together_client.py`)
- `USE_MOCK_LLM` (optional, 1 to use mock content)
- `DEBUG_LLM_OUTPUT` (optional, logs response length and tail)

### Run the Server
```bash
uvicorn app.main:app --reload --port 8000
```

### Open the Client
- Open `http://localhost:8000` in a browser.
- The client is served via FastAPI static files.

### Run Tests
```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Debugging / Troubleshooting

### Malformed JSON / Truncation
- Symptoms: parse errors, unbalanced braces, partial arrays.
- Fixes in code:
  - balanced JSON check
  - retry with higher `max_tokens`
  - repair prompt forcing JSON-only output
  - optional debug logging with `DEBUG_LLM_OUTPUT=1`

### Pydantic Type Errors
- Observed errors:
  - `intro_monologue` returned as a string
  - `props_list` returned as objects
- Mitigation: `_normalize_game_package()` coercion prior to validation.

### UI Issues (Resolved)
- Share code overflow fixed with wrapping and monospace styling.
- Clue IDs replaced with title/description via a clue lookup map.

### Host Modal Attempt (Reverted)
- A custom modal was attempted for host confirmation but reverted.
- Current behavior uses browser confirm dialogs for host access and solution reveal.

### Git Workflow (Recommended)
- Create a feature branch, push, open PR, merge to main.
- `.gitignore` excludes `.venv` and `.env` to protect secrets.

## Prompt Archive + AI Collaboration

### Prompt Files (server/prompts)
- `system_prompt.md`: safety constraints and JSON-only rule.
- `game_generation_prompt.md`: template-based generation instructions.
- `validation_prompt.md`: repair instructions for malformed/invalid JSON.
- `README_PROMPTS.md`: usage notes for prompt files.

### Prompt Strategy
- System prompt enforces PG-13 and JSON-only output.
- Generation prompt provides a full JSON template with fixed ids.
- Validation prompt repairs malformed or invalid structures without changing ids.

### AI Tool Usage
- Cursor: used for code iteration, refactors, and documentation updates.
- Together.ai: used to generate the narrative content.

## Security + Safety
- Secrets are stored in `.env` and excluded via `.gitignore`.
- `safety.py` runs a PG-13 keyword filter (`filter_or_raise`).
- Debug logging only emits response length/tail; avoid logging full payloads or keys.

## Known Limitations + Future Work
- LLM variability can still require repair passes.
- No persistent server-side storage (client uses localStorage).
- Host/player separation could be expanded (printable packets, PDF export).
- Add rate limiting, caching, and more categories.
- Improve UI accessibility and mobile layout.
# Project Manual

## MP1 -- Murder Mystery Party Generator

### Overview
This mini project provides a browser client and FastAPI server that generate a full
murder mystery party package using Together.ai. The system is deterministic when
provided a seed and share code, and it stores prompt templates for iteration.

### Current Project Review
- End-to-end flow works: browser inputs -> FastAPI -> Together.ai -> GamePackage JSON -> client render.
- Deterministic behavior is supported via seed + share code.
- Client supports player view, host view, export JSON, and share code copy/load.
- Host access uses browser confirm dialogs for safety prompts (no custom modal).
- Parsing/validation pipeline includes strict JSON parsing, retry/repair, and normalization
  to handle occasional LLM formatting drift.

### Architecture Diagram
```
Browser Client
  |
  |  POST /api/generate (player_count, category_id, tone, duration, seed)
  v
FastAPI Server (app.main)
  |
  |  TogetherClient -> Together.ai API
  v
GamePackage JSON -> Client renders + localStorage
```

### Endpoints
- `GET /health` -> `{ "ok": true }`
- `GET /api/categories` -> list of category objects
- `POST /api/generate` -> GamePackage JSON
- `POST /api/validate` -> validation issues (internal use)

### Client UX Summary
- Step 1: Players (count, optional names, seed/share code).
- Step 2: Theme (category selection or surprise).
- Step 3: Options (tone, duration).
- Step 4: Generate + Results (story, timeline, rounds, props, character packets).
- Host view is gated by a confirm prompt. Solution reveal is gated by confirm prompt.
- Export JSON downloads the latest game; share code can regenerate the same setup.

### Determinism and Validation
- A seeded PRNG governs category selection, ids, and clue assignment.
- LLM outputs are parsed strictly; malformed outputs trigger retry/repair.
- Validation enforces counts, ids, and relationship connectivity.
- Normalization coerces intro monologues, traits/secrets, and props into expected types.

### Environment and Debugging
- `TOGETHER_API_KEY` and optional `TOGETHER_MODEL` are required.
- `DEBUG_LLM_OUTPUT=1` logs response length, tail, and balance status.

### Prompt Archive Instructions
Prompts live in `server/prompts`:
- `system_prompt.md`: safety + JSON-only formatting
- `game_generation_prompt.md`: main generation template
- `validation_prompt.md`: repair prompt used when validation fails
- `README_PROMPTS.md`: explains how prompts are used

Update these files directly to iterate on LLM behavior without changing code.

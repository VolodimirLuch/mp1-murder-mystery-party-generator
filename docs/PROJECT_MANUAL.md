# Project Manual

## MP1 -- Murder Mystery Party Generator

### Overview
This mini project provides a browser client and FastAPI server that generate a full
murder mystery party package using Together.ai. The system is deterministic when
provided a seed and share code, and it stores prompt templates for iteration.

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

### Prompt Archive Instructions
Prompts live in `server/prompts`:
- `system_prompt.md`: safety + JSON-only formatting
- `game_generation_prompt.md`: main generation template
- `validation_prompt.md`: repair prompt used when validation fails
- `README_PROMPTS.md`: explains how prompts are used

Update these files directly to iterate on LLM behavior without changing code.

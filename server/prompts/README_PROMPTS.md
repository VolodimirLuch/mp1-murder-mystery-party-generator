# Prompt Archive

This folder stores the prompt templates used by the Together.ai generator.

- `system_prompt.md`: global safety and formatting rules (PG-13, JSON only).
- `game_generation_prompt.md`: main template for creating a full game package.
- `validation_prompt.md`: repair template used when validation fails.

The generator loads these files at runtime so you can iterate on prompt quality
without changing application code.

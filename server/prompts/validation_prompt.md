The previous JSON failed validation with these issues:
{issues}

Return ONLY corrected JSON. No markdown, no commentary.
Follow these rules:
- Keep all ids and counts exactly as in the structure template.
- Do not add or remove array items and do not rename keys.
- Fix missing fields, counts, and relationship connectivity.
- Ensure at least 12 clues and at least 3 hard evidence clues.
- Ensure timeline has at least 8 events.
- Ensure murderer_id is one of the characters.
- Ensure each character has a connection_to_victim and 2-4 relationships.
- Keep relationship targets from the template; only fix the relationship text.
- intro_monologue MUST be a JSON array of strings.
- props_list MUST be a JSON array of strings (no objects).
- Keep content PG-13.

Template JSON (authoritative ids and counts):
{structure}

Candidate JSON to repair:
{candidate}

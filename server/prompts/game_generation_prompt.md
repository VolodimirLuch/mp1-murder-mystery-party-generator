Generate a full murder mystery party package.
Output ONLY valid JSON. No markdown, no commentary, no YAML.

Category:
- Name: {category_name}
- Description: {category_description}
- Tone tags: {tone_tags}
- Suggested props: {suggested_props}
- Suggested archetypes: {suggested_archetypes}

Deterministic seed: {seed}

Instructions:
- Use the JSON structure below as a template.
- Keep all ids and counts exactly as provided (character_id, clue_id, event_id, round_id).
- Fill in all empty strings and empty arrays with complete content.
- Ensure relationships are 2-4 per character and describe the relationship text.
- Ensure clues include at least 3 hard evidence items and keep misleading clues plausible.
- Provide at least 8 timeline events and 3-5 rounds.
- Keep content PG-13 and avoid graphic details.
- intro_monologue MUST be a JSON array of strings.
- props_list MUST be a JSON array of strings (no objects).
- If running out of space, shorten text fields but NEVER break JSON and NEVER omit required keys.
- Storyline: 5-8 lines. Backstory: 2-4 sentences. Clue descriptions: 1-2 sentences.
- Intro monologue: 2-3 lines.

JSON Template:
{structure}

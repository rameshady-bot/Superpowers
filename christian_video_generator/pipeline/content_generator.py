"""
Anthropic-powered script generator.

Calls claude-sonnet-4-20250514 and returns a validated JSON script dict.
All interaction with the Anthropic API is confined to this module.
"""

import json
import os
import re

import anthropic

_SCHEMA_EXAMPLE = """{
  "theme": "string",
  "title": "string (max 8 words, in French)",
  "scripture": {
    "reference": "Book Chapter:Verse",
    "text": "Full verse in French (Louis Segond 21)"
  },
  "narration_segments": [
    {
      "segment_id": 1,
      "duration_seconds": 15,
      "text": "Narration text in French",
      "visual_keyword": "English 3-word Pexels search query",
      "mood": "peaceful|hopeful|joyful|reflective"
    }
  ],
  "background_music_mood": "calm|uplifting|reflective",
  "call_to_action": "One French closing sentence"
}"""

_SYSTEM_PROMPT = (
    "You are a French Christian video script writer. "
    "You output ONLY valid JSON — no markdown, no code fences, no explanations, "
    "no preamble, no trailing text. "
    "The JSON must exactly match this schema:\n"
    + _SCHEMA_EXAMPLE
    + "\n\nRules:\n"
    "- narration_segments must contain EXACTLY 5 segments.\n"
    "- The sum of all duration_seconds must be between 75 and 90 inclusive.\n"
    "- Each mood must be one of: peaceful, hopeful, joyful, reflective.\n"
    "- background_music_mood must be one of: calm, uplifting, reflective.\n"
    "- visual_keyword must be 2-4 English words suitable for a Pexels nature video search.\n"
    "- Scripture must be an actual Bible verse in Louis Segond 21 French translation.\n"
    "- title must be 8 words or fewer, in French.\n"
    "- All narration text must be in French."
)

_STRICT_SYSTEM_PROMPT = (
    _SYSTEM_PROMPT
    + "\n\nCRITICAL: Your previous response was not valid JSON. "
    "Output ONLY the raw JSON object. "
    "No ```json, no ```, no comments, no extra text whatsoever."
)

_VALID_MOODS = {"peaceful", "hopeful", "joyful", "reflective"}
_VALID_MUSIC_MOODS = {"calm", "uplifting", "reflective"}


def _strip_fences(raw: str) -> str:
    """Remove accidental markdown code fences from the model response."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _validate(data: dict) -> None:
    """Raise ValueError if the parsed dict does not satisfy the schema."""
    required_top = {"theme", "title", "scripture", "narration_segments",
                    "background_music_mood", "call_to_action"}
    missing = required_top - data.keys()
    if missing:
        raise ValueError(f"Script missing top-level keys: {missing}")

    sc = data["scripture"]
    if not isinstance(sc, dict) or "reference" not in sc or "text" not in sc:
        raise ValueError("scripture must have 'reference' and 'text' keys")

    segs = data["narration_segments"]
    if not isinstance(segs, list) or len(segs) != 5:
        raise ValueError(
            f"narration_segments must be a list of exactly 5 items, got {len(segs) if isinstance(segs, list) else type(segs)}"
        )

    seg_keys = {"segment_id", "duration_seconds", "text", "visual_keyword", "mood"}
    total_dur = 0
    for i, seg in enumerate(segs, 1):
        missing_k = seg_keys - seg.keys()
        if missing_k:
            raise ValueError(f"Segment {i} missing keys: {missing_k}")
        if seg["mood"] not in _VALID_MOODS:
            raise ValueError(f"Segment {i} has invalid mood '{seg['mood']}'")
        if not isinstance(seg["duration_seconds"], (int, float)) or seg["duration_seconds"] <= 0:
            raise ValueError(f"Segment {i} duration_seconds must be a positive number")
        total_dur += seg["duration_seconds"]

    if not (75 <= total_dur <= 90):
        raise ValueError(
            f"Total duration {total_dur}s is outside the required 75–90 s range"
        )

    if data["background_music_mood"] not in _VALID_MUSIC_MOODS:
        raise ValueError(
            f"background_music_mood '{data['background_music_mood']}' not in {_VALID_MUSIC_MOODS}"
        )


def _call_api(client: anthropic.Anthropic, theme: str, system: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Create a Christian encouragement video script on the theme: "
                    f'"{theme}". Return ONLY the JSON object.'
                ),
            }
        ],
    )
    return message.content[0].text


def generate_script(theme: str) -> dict:
    """
    Call the Anthropic API and return a validated script dict.

    Retries once with a stricter prompt if JSON parsing fails.
    Raises ValueError if both attempts fail.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file or export it before running."
        )

    client = anthropic.Anthropic(api_key=api_key)

    # First attempt
    raw = _call_api(client, theme, _SYSTEM_PROMPT)
    cleaned = _strip_fences(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        print("  [content] First parse failed — retrying with stricter prompt…")
        raw = _call_api(client, theme, _STRICT_SYSTEM_PROMPT)
        cleaned = _strip_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"API returned invalid JSON after two attempts.\n"
                f"JSONDecodeError: {exc}\n"
                f"Raw response (last attempt):\n{raw}"
            ) from exc

    _validate(data)
    return data

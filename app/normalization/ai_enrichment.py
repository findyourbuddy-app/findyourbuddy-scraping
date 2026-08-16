import logging
import json
import httpx
from app.normalization.schema import EventPayload

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = [
    "running", "coffee", "concert", "climbing", "hiking",
    "cycling", "yoga", "boardgames", "football", "party",
    "theatre", "art", "workshop", "hobby", "other"
]

def enrich_event_with_ai(payload: EventPayload, api_key: str, model: str) -> EventPayload:
    """Enriches an EventPayload with AI-determined category mapping and tags using Gemini API."""
    if not api_key:
        logger.debug("GEMINI_API_KEY is not set. Skipping AI enrichment.")
        return payload

    prompt = (
        "You are an AI assistant that categorizes and enriches social events.\n"
        "Categorize the event into exactly one of these allowed categories:\n"
        f"{json.dumps(ALLOWED_CATEGORIES)}\n\n"
        "Also, extract up to 5 sub-interest tags or music genres (e.g. 'techno', 'rock', 'classical', 'exhibition', 'craft beer') "
        "relevant to the event.\n\n"
        f"Event Title: {payload.title}\n"
        f"Event Description: {payload.description or ''}\n\n"
        "Return ONLY a raw JSON object matching this structure (no markdown formatting, no code blocks):\n"
        "{\n"
        '  "category": "concert",\n'
        '  "tags": ["techno", "electronic", "dance"]\n'
        "}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=5.0)
        if response.status_code == 200:
            result = response.json()
            text_response = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            parsed = json.loads(text_response)
            
            # Map category if valid
            new_category = parsed.get("category")
            if new_category in ALLOWED_CATEGORIES:
                payload.category = new_category
                
            # Append tags to description
            tags = parsed.get("tags", [])
            if tags:
                tag_line = ", ".join(tags)
                desc = payload.description or ""
                payload.description = f"{desc}\n\nTags: {tag_line}".strip()
                
            logger.info(f"AI Enrichment successful for: {payload.title} (Mapped to {payload.category})")
        else:
            logger.warning(f"Gemini API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to enrich event with AI: {e}")

    return payload

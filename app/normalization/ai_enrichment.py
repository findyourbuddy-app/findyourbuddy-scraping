import json
import logging
import re
import httpx
from app.normalization.schema import EventPayload

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = [
    "running", "coffee", "concert", "climbing", "hiking",
    "cycling", "yoga", "boardgames", "football", "party",
    "theatre", "art", "workshop", "hobby", "other"
]


def _clean_json_str(raw_text: str) -> str:
    cleaned = re.sub(r"```json\s*", "", raw_text)
    cleaned = re.sub(r"```\s*", "", cleaned)
    return cleaned.strip()


def enrich_event_with_novita(
    payload: EventPayload,
    api_key: str,
    base_url: str = "https://api.novita.ai/v3/openai",
    model: str = "deepseek/deepseek-r1-distill-llama-70b"
) -> EventPayload:
    """Enriches an EventPayload with AI-determined category mapping and tags using Novita AI OpenAI-compatible API."""
    if not api_key:
        logger.debug("NOVITA_API_KEY is not set. Skipping Novita AI enrichment.")
        return payload

    prompt = (
        "You are an AI assistant that categorizes and enriches social events.\n"
        "Categorize the event into exactly one of these allowed categories:\n"
        f"{json.dumps(ALLOWED_CATEGORIES)}\n\n"
        "Also, extract up to 5 sub-interest tags or music genres (e.g. 'techno', 'rock', 'exhibition', 'craft beer') "
        "relevant to the event.\n\n"
        f"Event Title: {payload.title}\n"
        f"Event Description: {payload.description or ''}\n\n"
        "Return ONLY a raw JSON object with keys 'category' and 'tags'. Example:\n"
        '{"category": "concert", "tags": ["techno", "electronic"]}'
    )

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You output JSON only."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=8.0)
        if response.status_code == 200:
            res_data = response.json()
            content = res_data["choices"][0]["message"]["content"]
            parsed = json.loads(_clean_json_str(content))

            new_category = parsed.get("category")
            if new_category in ALLOWED_CATEGORIES:
                payload.category = new_category

            tags = parsed.get("tags", [])
            if tags:
                tag_line = ", ".join(tags)
                desc = payload.description or ""
                payload.description = f"{desc}\n\nEtiketler: {tag_line}".strip()

            logger.info(f"Novita AI Enrichment successful for: {payload.title} -> {payload.category}")
        else:
            logger.warning(f"Novita API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to enrich event with Novita AI: {e}")

    return payload


def enrich_event_with_ai(payload: EventPayload, api_key: str, model: str) -> EventPayload:
    """Fallback Gemini API enrichment."""
    if not api_key:
        return payload

    prompt = (
        "You are an AI assistant that categorizes social events.\n"
        f"Allowed categories: {json.dumps(ALLOWED_CATEGORIES)}\n"
        f"Title: {payload.title}\nDescription: {payload.description or ''}\n"
        'Return JSON: {"category": "concert", "tags": ["rock"]}'
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=5.0)
        if response.status_code == 200:
            result = response.json()
            text_response = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            parsed = json.loads(_clean_json_str(text_response))

            new_category = parsed.get("category")
            if new_category in ALLOWED_CATEGORIES:
                payload.category = new_category

            tags = parsed.get("tags", [])
            if tags:
                tag_line = ", ".join(tags)
                desc = payload.description or ""
                payload.description = f"{desc}\n\nEtiketler: {tag_line}".strip()
    except Exception as e:
        logger.error(f"Gemini AI enrichment error: {e}")

    return payload

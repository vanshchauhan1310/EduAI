# app/ai/tutor/image_search.py
"""
"Concept media" — find images, generate SVG diagrams, and suggest YouTube
educational videos for a CBSE Class 10 topic.

Three-tier media strategy:
  1. **Gemini SVG diagrams** — generates vector educational diagrams on-demand
  2. **Wikimedia Commons images** — free CC-licensed educational diagrams
  3. **YouTube video search links** — using Gemini to suggest relevant educational videos

All failures are swallowed — never breaks the lesson/chat flow.
"""

import base64
import logging
import re
from functools import lru_cache
from typing import Dict, List, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
_IMAGE_MIME_PREFIXES = ("image/jpeg", "image/png", "image/svg+xml", "image/gif")
_TIMEOUT = 10
_GEMINI_TIMEOUT = 30

_UA = "EduAI-Tutor/1.0 (educational use)"
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-1.5-flash",
    "gemini-2.0-flash-exp",
]

# Google Search grounding (the "google_search" tool) is only available on
# Gemini 2.0+ models — keep a separate list so we don't waste calls on 1.5.
_GEMINI_SEARCH_MODELS = [
    "gemini-flash-latest",
    "gemini-2.0-flash-exp",
]

_IMAGE_URL_RE = re.compile(r'\.(jpe?g|png|svg|webp|gif)(\?[^\s"]*)?$', re.IGNORECASE)

_IMAGE_TRIGGERS = {
    # English
    "diagram", "image", "picture", "illustration", "drawing", "figure",
    "graph", "chart", "visual", "show", "photo",
    # Telugu — so the language picker (English/Telugu/Both) doesn't change
    # whether image recommendations get attached
    "చిత్రం", "బొమ్మ", "రేఖాచిత్రం", "ఫోటో", "చూపించు", "చూపించండి",
}

_VIDEO_TRIGGERS = {
    # English
    "video", "tutorial", "watch", "youtube", "lesson", "explain", "demonstrate",
    "show me", "how to", "animation",
    # Telugu — same reasoning as _IMAGE_TRIGGERS
    "వీడియో", "యూట్యూబ్", "చూడండి", "వివరించండి", "వివరించు", "నేర్పించు",
}


def _wants_image(question: str) -> bool:
    q = question.lower()
    return any(trigger in q for trigger in _IMAGE_TRIGGERS)


def _wants_video(question: str) -> bool:
    q = question.lower()
    return any(trigger in q for trigger in _VIDEO_TRIGGERS)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _attribution(extmetadata: Dict) -> str:
    artist = (extmetadata.get("Artist", {}) or {}).get("value", "") or ""
    artist = re.sub(r"<[^>]+>", "", artist).strip()
    license_name = (extmetadata.get("LicenseShortName", {}) or {}).get("value", "") or ""
    parts = [p for p in (artist, license_name) if p]
    return " · ".join(parts) if parts else "Wikimedia Commons"


def _to_concept_image(page: Dict) -> Optional[Dict]:
    info_list = page.get("imageinfo") or []
    if not info_list:
        return None
    info = info_list[0]
    mime = (info.get("mime") or "").lower()
    if not any(mime.startswith(prefix) for prefix in _IMAGE_MIME_PREFIXES):
        return None
    extmetadata = info.get("extmetadata") or {}
    title = page.get("title", "").replace("File:", "").rsplit(".", 1)[0]
    return {
        "title": title,
        "thumbnail_url": info.get("thumburl") or info.get("url", ""),
        "full_url": info.get("url", ""),
        "attribution": _attribution(extmetadata),
        "source_url": info.get("descriptionurl", ""),
    }


# ── Image sources ───────────────────────────────────────────────────────────

def _search_commons(query: str, limit: int = 4) -> List[Dict]:
    """Search Wikimedia Commons for images matching the query."""
    try:
        params = {
            "action": "query", "format": "json", "generator": "search",
            "gsrnamespace": 6, "gsrsearch": query,
            "gsrlimit": max(limit * 2, 10),
            "prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": 320,
        }
        resp = requests.get(COMMONS_API, params=params, timeout=_TIMEOUT,
                            headers={"User-Agent": _UA})
        resp.raise_for_status()
        pages = (resp.json().get("query") or {}).get("pages") or {}
        images = []
        for page in pages.values():
            image = _to_concept_image(page)
            if image and image["thumbnail_url"]:
                images.append(image)
        return images[:limit]
    except Exception as exc:
        logger.debug("Commons search failed for '%s': %s", query, exc)
        return []


def _gemini_svg_diagram(concept: str) -> Optional[str]:
    """Generate an SVG educational diagram using Gemini."""
    if not settings.GEMINI_API_KEY:
        return None

    prompt = (
        f"Generate a clean, good-looking SVG educational diagram explaining the "
        f"CBSE Class 10 concept '{concept}', as if for a textbook illustration.\n"
        f"Requirements:\n"
        f"- Output ONLY raw SVG code — no markdown fences, no commentary.\n"
        f"- viewBox='0 0 400 300', white (#ffffff) background rectangle behind everything.\n"
        f"- Use a simple, consistent, pleasant palette (e.g. soft blues/greens/oranges) "
        f"with clear black outlines (stroke-width 1.5-2) — avoid harsh or clashing colors.\n"
        f"- Lay elements out with generous spacing so nothing overlaps; align labels "
        f"neatly next to (not on top of) the shapes/arrows they describe.\n"
        f"- Use a readable sans-serif font-family (e.g. 'Arial, sans-serif'), "
        f"font-size 12-14 for labels and 16-18 for the title.\n"
        f"- Include a short title at the top, clearly labelled parts/arrows, and any "
        f"key formula written in plain characters (no LaTeX) near the relevant part.\n"
        f"- Keep it minimal and uncluttered — only what's needed to explain the idea.\n"
        f"Start with <svg and end with </svg>."
    )

    for model in _GEMINI_MODELS:
        url = f"{_GEMINI_BASE}/{model}:generateContent"
        try:
            resp = requests.post(
                f"{url}?key={settings.GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2000},
                },
                timeout=_GEMINI_TIMEOUT,
            )
            if resp.status_code == 503:
                continue
            if not resp.ok:
                continue
            text = (resp.json().get("candidates", [{}])[0]
                    .get("content", {}).get("parts", [{}])[0].get("text", ""))
            svg_match = re.search(r'<svg[\s\S]*?</svg>', text, re.IGNORECASE)
            if svg_match and len(svg_match.group()) > 100:
                logger.info("Gemini %s generated SVG for '%s' (%d chars)",
                            model, concept, len(svg_match.group()))
                return base64.b64encode(svg_match.group().encode()).decode()
        except Exception:
            continue
    return None


# ── Gemini + Google Search grounded image lookup ────────────────────────────

def _gemini_grounded_images(concept: str, limit: int = 4) -> List[Dict]:
    """
    Ask Gemini — with the Google Search tool enabled (grounding) — to find real,
    topic-related image URLs out on the web. Best-effort: any malformed/non-image
    URL is dropped, and an empty list lets the caller fall through to Commons.
    """
    if not settings.GEMINI_API_KEY:
        return []

    prompt = (
        f"Use Google Search to find {limit} real educational images (diagrams, "
        f"photos, or illustrations) for the CBSE Class 10 concept '{concept}'. "
        f"For each result, give: a short title, a direct image URL (image_url) "
        f"ending in .jpg, .jpeg, .png, .svg, .webp or .gif, and the source webpage "
        f"URL (source_url). Return ONLY a JSON array of objects with keys: "
        f"title, image_url, source_url."
    )

    for model in _GEMINI_SEARCH_MODELS:
        url = f"{_GEMINI_BASE}/{model}:generateContent"
        try:
            resp = requests.post(
                f"{url}?key={settings.GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "tools": [{"google_search": {}}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
                },
                timeout=_GEMINI_TIMEOUT,
            )
            if resp.status_code == 503 or not resp.ok:
                continue
            text = (resp.json().get("candidates", [{}])[0]
                    .get("content", {}).get("parts", [{}])[0].get("text", ""))
            arr_match = re.search(r'\[[\s\S]*?\]', text)
            if not arr_match:
                continue
            import json
            items = json.loads(arr_match.group())
            if not isinstance(items, list):
                continue

            images = []
            for item in items[:limit]:
                if not isinstance(item, dict):
                    continue
                image_url = str(item.get("image_url", "")).strip()
                if not image_url.startswith(("http://", "https://")) or not _IMAGE_URL_RE.search(image_url):
                    continue
                images.append({
                    "title": str(item.get("title") or concept)[:100],
                    "thumbnail_url": image_url,
                    "full_url": image_url,
                    "attribution": "Found via Google Search · Gemini AI",
                    "source_url": str(item.get("source_url", ""))[:300],
                })
            if images:
                logger.info("Gemini %s found %d grounded images for '%s'",
                            model, len(images), concept)
                return images
        except Exception:
            continue
    return []


# ── YouTube video suggestions via Gemini ─────────────────────────────────────

def _gemini_youtube_suggestions(concept: str) -> List[Dict]:
    """
    Use Gemini to suggest relevant YouTube educational videos for the concept.
    Returns a list of {title, channel, url} dicts with YouTube search/play URLs.
    """
    if not settings.GEMINI_API_KEY:
        return []

    prompt = (
        f"Suggest 2 educational YouTube videos about the CBSE Class 10 concept "
        f"'{concept}'. For each, provide: title, channel name, and a search URL "
        f"like https://www.youtube.com/results?search_query=SEARCH_TERMS_HERE "
        f"(use English keywords suitable for the concept). "
        f"Return ONLY a JSON array with objects having keys: title, channel, url."
    )

    for model in _GEMINI_MODELS:
        url = f"{_GEMINI_BASE}/{model}:generateContent"
        try:
            resp = requests.post(
                f"{url}?key={settings.GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500},
                },
                timeout=_GEMINI_TIMEOUT,
            )
            if resp.status_code == 503:
                continue
            if not resp.ok:
                continue
            text = (resp.json().get("candidates", [{}])[0]
                    .get("content", {}).get("parts", [{}])[0].get("text", ""))
            # Extract JSON array
            arr_match = re.search(r'\[[\s\S]*?\]', text)
            if arr_match:
                import json
                items = json.loads(arr_match.group())
                if isinstance(items, list):
                    # Validate and clean
                    videos = []
                    for item in items[:2]:
                        if isinstance(item, dict) and item.get("title") and item.get("url"):
                            videos.append({
                                "title": str(item["title"])[:100],
                                "channel": str(item.get("channel", "YouTube"))[:60],
                                "url": str(item["url"]),
                            })
                    if videos:
                        logger.info("Gemini suggested %d YouTube videos for '%s'",
                                    len(videos), concept)
                        return videos
        except Exception:
            continue
    return []


# ── Commons search strategies ────────────────────────────────────────────────

def _search_strategies(concept: str) -> List[str]:
    base = concept.strip()
    strategies = [base]
    words = base.split()
    if len(words) > 2:
        strategies.append(" ".join(words[:2]))
    if "law" in base.lower():
        strategies.append(base.lower().replace("law", "").strip())
    strategies.append(f"{base} CBSE")
    strategies.append(f"{base} diagram")
    if "ohm" in base.lower():
        strategies.append("electric circuit diagram")
    if "light" in base.lower() or "lens" in base.lower() or "mirror" in base.lower():
        strategies.append("light reflection refraction diagram")
    if "trig" in base.lower():
        strategies.append("trigonometry triangle")
    if "quadrat" in base.lower():
        strategies.append("quadratic equation graph")
    if "acid" in base.lower() or "base" in base.lower():
        strategies.append("pH scale diagram")
    return strategies


# ── Main public API ──────────────────────────────────────────────────────────

@lru_cache(maxsize=128)
def search_concept_images(
    query: str,
    limit: int = 4,
    user_requested_image: bool = False,
) -> List[Dict]:
    """
    Best-effort image search: Gemini SVG → Gemini+Google Search grounding → Commons fallback.
    Returns list of ConceptImage dicts (never blocks).
    """
    query = (query or "").strip()
    if not query:
        return []

    results: List[Dict] = []

    # 1. Gemini SVG (when user explicitly asks for image/diagram)
    if user_requested_image and settings.GEMINI_API_KEY:
        svg_b64 = _gemini_svg_diagram(query)
        if svg_b64:
            results.append({
                "title": f"{query} — Educational Diagram",
                "thumbnail_url": f"data:image/svg+xml;base64,{svg_b64}",
                "full_url": f"data:image/svg+xml;base64,{svg_b64}",
                "attribution": "Generated by Gemini AI · Educational diagram",
                "source_url": "",
            })
            return results  # SVG is best, return immediately

    # 2. Gemini + Google Search grounding — real topic-related images from the web
    if not results and settings.GEMINI_API_KEY:
        try:
            results.extend(_gemini_grounded_images(query, limit=limit))
        except Exception:
            pass

    # 3. Commons fallback
    if not results:
        seen_urls: set = set()
        for sq in _search_strategies(query):
            if len(results) >= limit:
                break
            try:
                for img in _search_commons(sq, limit - len(results) + 2):
                    url = img.get("full_url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        results.append(img)
                        if len(results) >= limit:
                            break
            except Exception:
                continue

    return results


def search_concept_videos(concept: str) -> List[Dict]:
    """
    Best-effort YouTube video search via Gemini suggestions.
    Returns list of {title, channel, url} dicts.
    """
    concept = (concept or "").strip()
    if not concept or not settings.GEMINI_API_KEY:
        return []

    # Always provide a default YouTube search URL as fallback
    search_url = (
        f"https://www.youtube.com/results?search_query="
        f"{requests.utils.quote(f'{concept} CBSE Class 10')}"
    )

    try:
        videos = _gemini_youtube_suggestions(concept)
        if videos:
            return videos
    except Exception:
        pass

    # Fallback: return a YouTube search URL
    return [{
        "title": f"Search YouTube for \"{concept}\"",
        "channel": "YouTube",
        "url": search_url,
    }]
# app/ai/tutor/llm_client.py
"""
Chat-completion provider for the AI Tutor.

Two backends with automatic fallback:
  1. NVIDIA NIM (preferred — fast 70B model, streaming SSE)
  2. HuggingFace Inference (fallback — used when NIM fails or key is absent)

Callers just send/receive plain {"role", "content"} message dicts —
no LangChain dependency, mirroring the raw-requests style already used in exam_prep.
"""

import json
import logging
import re
from typing import Dict, List, Optional

import httpx
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def using_real_llm() -> bool:
    return bool(settings.HF_API_TOKEN or settings.NVIDIA_NIM_API_KEY)


def extract_json(text: str) -> str:
    """Strip code fences and slice out the outermost {{...}} object."""
    t = _FENCE_RE.sub("", text or "").strip()
    start, end = t.find("{"), t.rfind("}")
    return t[start:end + 1] if start != -1 and end > start else t


def parse_json(text: str) -> Dict:
    """Tolerant JSON parse: extract the JSON object, repair common LLM slip-ups
    (trailing commas, single quotes) if a strict parse fails."""
    raw = extract_json(text)
    try:
        return json.loads(raw)
    except Exception:
        repaired = re.sub(r",\s*([}\]])", r"\1", raw)  # drop trailing commas
        return json.loads(repaired)


class TutorLLMClient:
    """Stateless chat-completion client with HF-first, NIM-fallback."""

    def __init__(self):
        self._hf_client: Optional["InferenceClient"] = None
        self._nim_url: Optional[str] = None
        self._nim_headers: Optional[Dict[str, str]] = None

        # --- HuggingFace (preferred) ---
        if settings.HF_API_TOKEN:
            try:
                from huggingface_hub import InferenceClient
                self._hf_client = InferenceClient(
                    model=settings.HF_MODEL,
                    token=settings.HF_API_TOKEN,
                )
                logger.info("HF Inference client ready for %s", settings.HF_MODEL)
            except Exception as exc:
                logger.warning("Failed to init HF client: %s — will use NIM fallback", exc)

        # --- NVIDIA NIM (primary) ---
        if settings.NVIDIA_NIM_API_KEY:
            self._nim_url = f"{settings.NVIDIA_NIM_BASE_URL.rstrip('/')}/chat/completions"
            self._nim_headers = {
                "Authorization": f"Bearer {settings.NVIDIA_NIM_API_KEY}",
                "Content-Type": "application/json",
            }
            logger.info("NVIDIA NIM primary client ready (%s)", settings.NVIDIA_NIM_MODEL)

        if not self._hf_client and not self._nim_url:
            raise RuntimeError(
                "Neither HF_API_TOKEN nor NVIDIA_NIM_API_KEY is configured in "
                "backend/.env — the AI Tutor needs at least one working LLM provider."
            )

    @property
    def using_real_llm(self) -> bool:
        return using_real_llm()

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: int = 2000,
    ) -> str:
        # Try NVIDIA NIM first (preferred provider).
        if self._nim_url:
            try:
                return self._chat_nim(messages, temperature, max_tokens)
            except Exception as exc:
                logger.warning(
                    "NIM call failed (%s: %s) — falling back to HuggingFace",
                    type(exc).__name__, exc,
                )

        # Fall back to HuggingFace.
        if self._hf_client:
            try:
                return self._chat_hf(messages, temperature, max_tokens)
            except Exception as exc:
                logger.error("HuggingFace fallback also failed: %s", exc)
                raise

        raise RuntimeError("No LLM provider available — both NIM and HF are unconfigured.")

    def _chat_hf(self, messages, temperature, max_tokens) -> str:
        completion = self._hf_client.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content or ""

    def _chat_nim(self, messages, temperature, max_tokens) -> str:
        # Use SSE streaming so the connection stays alive while the model generates
        # tokens instead of waiting for the full response body. The per-read timeout
        # (120 s) prevents a stalled stream from hanging forever.
        parts: List[str] = []
        timeout = httpx.Timeout(connect=15.0, read=120.0, write=15.0, pool=15.0)
        with httpx.Client(timeout=timeout) as client:
            with client.stream(
                "POST", self._nim_url,
                headers=self._nim_headers,
                json={
                    "model": settings.NVIDIA_NIM_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    if line == "data: [DONE]":
                        break
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0]["delta"].get("content") or ""
                            parts.append(delta)
                        except Exception:
                            continue
        return "".join(parts)


_client: TutorLLMClient | None = None


def get_llm_client() -> TutorLLMClient:
    """Lazily-built singleton — avoids constructing the HF/NIM client (and raising
    on a missing key) at import time, e.g. during Alembic autogenerate or tests."""
    global _client
    if _client is None:
        _client = TutorLLMClient()
    return _client
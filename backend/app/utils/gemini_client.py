"""
AI Client — uses NVIDIA NIM API for all Admin Copilot features.
NVIDIA NIM is OpenAI-compatible, so we use the openai SDK with NVIDIA's base URL.

Setup:
  1. Get free API key at: https://build.nvidia.com/  (1000 free credits, no card needed)
  2. Set NVIDIA_NIM_API_KEY=nvapi-... in .env
  3. Set NVIDIA_NIM_MODEL in .env (default: meta/llama-3.3-70b-instruct)
"""
import json
import os
import re
from pathlib import Path
from openai import AsyncOpenAI, APIConnectionError, AuthenticationError, RateLimitError
from fastapi import HTTPException, status
from dotenv import load_dotenv

from app.core.config import settings

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _get_nim_setting(name: str, default: str = "") -> str:
    return getattr(settings, name, None) or os.getenv(name, default)


def _get_client() -> AsyncOpenAI:
    api_key = _get_nim_setting("NVIDIA_NIM_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NVIDIA_NIM_API_KEY is not configured in backend/.env.",
        )
    return AsyncOpenAI(
        base_url=_get_nim_setting("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        api_key=api_key,
    )


def _extract_json(text: str) -> dict:
    """Strip markdown fences and parse JSON from model output."""
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]
    return json.loads(cleaned)


def _handle_nim_error(e: Exception) -> None:
    """Convert NVIDIA NIM errors to meaningful FastAPI HTTP exceptions."""
    if isinstance(e, AuthenticationError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "NVIDIA NIM API key is invalid. "
                "Get a free key at: https://build.nvidia.com/"
            ),
        )
    if isinstance(e, RateLimitError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NVIDIA NIM rate limit reached. Wait a moment and retry.",
        )
    if isinstance(e, APIConnectionError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to NVIDIA NIM API. Check your internet connection.",
        )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"NVIDIA NIM error: {str(e)[:300]}",
    )


async def generate_text(prompt: str) -> str:
    """Call NVIDIA NIM and return plain text response."""
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=_get_nim_setting("NVIDIA_NIM_MODEL", "meta/llama-3.3-70b-instruct"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content.strip()
    except (AuthenticationError, RateLimitError, APIConnectionError) as e:
        _handle_nim_error(e)
    except Exception as e:
        _handle_nim_error(e)


async def generate_json(prompt: str) -> dict:
    """Call NVIDIA NIM and parse the response as JSON."""
    full_prompt = (
        prompt
        + "\n\nCRITICAL INSTRUCTION: Return ONLY a valid JSON object. "
        "No explanation text, no markdown code fences, no ```json blocks. "
        "Start your response with { and end with }."
    )
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=_get_nim_setting("NVIDIA_NIM_MODEL", "meta/llama-3.3-70b-instruct"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a data extraction assistant. Always respond with valid JSON only.",
                },
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()
        return _extract_json(raw)
    except (AuthenticationError, RateLimitError, APIConnectionError) as e:
        _handle_nim_error(e)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model returned invalid JSON: {e}",
        )
    except Exception as e:
        _handle_nim_error(e)


# ─── Prompt Templates ─────────────────────────────────────────────

CIRCULAR_SUMMARY_PROMPT = """You are an expert government education administrator in Andhra Pradesh, India.
Analyze the following government circular and extract structured information.

CIRCULAR TEXT:
{text}

Return a JSON object with EXACTLY these keys:
- "summary": 2-3 sentence executive summary of the circular
- "key_instructions": array of main instructions (each a short string)
- "action_items": array of specific actions required from schools/officers
- "deadlines": array of deadline entries (date + action)
- "responsible_officers": array of officer designations/roles mentioned
- "compliance_requirements": array of compliance or reporting requirements

Return ONLY valid JSON, no markdown."""


LETTER_GENERATION_PROMPT = """You are an expert in generating official government letters for the Education Department of Andhra Pradesh, India.

Generate a formal official letter with the following details:
Template Type: {letter_type_name}

Form Data:
{fields_formatted}

Output Language: English

Requirements:
1. Use official Indian government letter format
2. Include: Reference Number (auto-generate as EDU/YYYY/NNNN format), Date (today), To/From sections
3. Include proper Subject line, formal letter body, and signature block
4. Use respectful, formal government language

Return the complete letter text as plain text with proper line breaks. Do NOT wrap in JSON."""


REPORT_GENERATION_PROMPT = """You are a senior education data analyst for the Government of Andhra Pradesh.

Generate a comprehensive {report_type_name} based on the following data:

REPORT DATA:
{data_formatted}

Output Language: English

Generate a structured JSON report with these exact keys:
- "executive_summary": 3-4 sentence overview of overall status
- "kpi_analysis": analysis of key performance indicators with specific numbers
- "trends": observations about trends over time
- "risks": identified risk areas requiring attention
- "recommendations": array of specific actionable recommendation strings (at least 5)
- "action_plan": array of simple action-step strings with suggested timelines

Use only strings inside the lists for recommendations and action_plan. Be specific with numbers. Return ONLY valid JSON."""



TRANSLATION_PROMPT = """You are an expert translator specializing in official government education documents for Andhra Pradesh.

Translate the following text from {source_language} to {target_language}.
Maintain the formal, official tone appropriate for government education documents.
Preserve any proper nouns, designations, and official terms accurately.

TEXT TO TRANSLATE:
{text}

Return ONLY the translated text — no explanations, no headers, no extra content."""

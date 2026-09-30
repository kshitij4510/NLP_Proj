"""
LLM service — provider-agnostic interface for language generation.
Supports: demo (no LLM), OpenAI, Google Gemini, local HuggingFace.
LLM output is always tagged as INTERPRETATION — never silently promoted to EVIDENCE.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Demo responses ensure the system works without any API keys
_DEMO_JSON = {"summary": "Demo mode — no LLM configured.", "key_findings": [], "method_trends": [], "limitations": []}
_DEMO_TEXT = "Demo mode — configure LLM_PROVIDER in .env to enable AI-generated text."
_DEMO_LIST: List[dict] = []


class LLMService:
    """
    Provider-agnostic LLM interface.
    In demo mode all methods return safe placeholder responses — the system
    remains fully functional for structure/pipeline testing without API keys.
    """

    def __init__(self) -> None:
        self._provider = settings.LLM_PROVIDER

    async def generate_text(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate plain text. Always tagged INTERPRETATION upstream."""
        if self._provider == "demo":
            return _DEMO_TEXT
        try:
            if self._provider == "openai":
                return await self._openai_text(prompt, max_tokens)
            if self._provider == "gemini":
                return await self._gemini_text(prompt, max_tokens)
            return _DEMO_TEXT
        except Exception as exc:
            logger.error("llm.generate_text.error", provider=self._provider, error=str(exc))
            raise LLMError(f"LLM text generation failed: {exc}") from exc

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """Generate and parse a JSON object."""
        if self._provider == "demo":
            return _DEMO_JSON.copy()
        raw = await self.generate_text(prompt + "\n\nRespond with valid JSON only.")
        return self._parse_json(raw) or _DEMO_JSON.copy()

    async def generate_json_list(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate and parse a JSON array."""
        if self._provider == "demo":
            return list(_DEMO_LIST)
        raw = await self.generate_text(prompt + "\n\nRespond with a valid JSON array only.")
        parsed = self._parse_json(raw)
        if isinstance(parsed, list):
            return parsed
        return []

    # ── Provider implementations ──────────────

    async def _openai_text(self, prompt: str, max_tokens: int) -> str:
        import openai
        client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    async def _gemini_text(self, prompt: str, max_tokens: int) -> str:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = await model.generate_content_async(prompt)
        return response.text or ""

    # ── Utilities ─────────────────────────────

    @staticmethod
    def _parse_json(raw: str) -> Any:
        raw = raw.strip()
        # Strip markdown code fences if present
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if match:
            raw = match.group(1).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("llm.json_parse_failed", raw_snippet=raw[:200])
            return None

"""Verify the configured Gemini provider without displaying credentials."""
import asyncio, sys
from pathlib import Path
from dotenv import load_dotenv
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
load_dotenv(root / ".env.local", override=True)
from app.core.config import settings
from app.services.llm_service import LLMService
async def main():
    if not settings.GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY is not configured in backend/.env.local")
    settings.LLM_PROVIDER = "gemini"
    text = await LLMService().generate_text("Reply with exactly: CONNECTION_OK", max_tokens=128)
    if "CONNECTION_OK" not in text:
        raise SystemExit("Provider replied, but the verification response was unexpected")
    print("Gemini live verification passed. Model: " + settings.GEMINI_MODEL)
if __name__ == "__main__":
    asyncio.run(main())

import pytest
from app.core.config import settings
from app.core.exceptions import LLMError
from app.services.llm_service import LLMService

@pytest.mark.asyncio
@pytest.mark.parametrize("provider,key",[("openai","OPENAI_API_KEY"),("gemini","GEMINI_API_KEY")])
async def test_missing_provider_credentials_are_explicit(monkeypatch,provider,key):
    monkeypatch.setattr(settings,"LLM_PROVIDER",provider)
    monkeypatch.setattr(settings,key,None)
    with pytest.raises(LLMError,match=key): await LLMService().generate_text("Verification")

@pytest.mark.asyncio
async def test_unsupported_provider_cannot_silently_use_demo(monkeypatch):
    monkeypatch.setattr(settings,"LLM_PROVIDER","local")
    with pytest.raises(LLMError,match="Unsupported LLM provider"): await LLMService().generate_text("Verification")

@pytest.mark.asyncio
async def test_invalid_provider_json_is_not_fake_success(monkeypatch):
    monkeypatch.setattr(settings,"LLM_PROVIDER","openai")
    async def invalid(self,prompt,max_tokens=2000): return "not JSON"
    monkeypatch.setattr(LLMService,"generate_text",invalid)
    with pytest.raises(LLMError,match="invalid JSON object"): await LLMService().generate_json("Verification")

def test_worker_uses_configured_redis_dsn():
    from app.workers.main import WorkerSettings
    from arq.connections import RedisSettings
    expected=RedisSettings.from_dsn(settings.REDIS_URL)
    assert WorkerSettings.redis_settings.host==expected.host
    assert WorkerSettings.redis_settings.port==expected.port
    assert WorkerSettings.redis_settings.password==expected.password

@pytest.mark.asyncio
async def test_gemini_request_and_response_contract(monkeypatch):
    import json, httpx
    monkeypatch.setattr(settings,"LLM_PROVIDER","gemini")
    monkeypatch.setattr(settings,"GEMINI_API_KEY","test-key")
    real_client=httpx.AsyncClient
    def handler(request):
        assert str(request.url)=="https://generativelanguage.googleapis.com/v1beta/interactions"
        assert request.headers["x-goog-api-key"]=="test-key"
        body=json.loads(request.content)
        assert body["input"]=="Verification" and body["store"] is False
        assert body["generation_config"]["max_output_tokens"]==500
        return httpx.Response(200,json={"steps":[{"type":"model_output","content":[{"type":"text","text":"Verified adapter response"}]}]})
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kwargs:real_client(transport=httpx.MockTransport(handler),**kwargs))
    assert await LLMService().generate_text("Verification",max_tokens=500)=="Verified adapter response"

@pytest.mark.asyncio
async def test_gemini_empty_response_is_failure(monkeypatch):
    import httpx
    monkeypatch.setattr(settings,"LLM_PROVIDER","gemini")
    monkeypatch.setattr(settings,"GEMINI_API_KEY","test-key")
    real_client=httpx.AsyncClient
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kwargs:real_client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={"steps":[]})),**kwargs))
    with pytest.raises(LLMError,match="no text output"): await LLMService().generate_text("Verification")

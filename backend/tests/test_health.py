import asyncio
from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app
from app.services.health import HealthSnapshot


class FakeHealthService:
    def check(self) -> HealthSnapshot:
        return HealthSnapshot(sqlite="ok", qdrant="unavailable", ollama="ok")


def test_health_reports_api_and_configuration_without_secrets() -> None:
    app = create_app(
        SimpleNamespace(
            settings=Settings(),
            health=FakeHealthService(),
        )
    )

    async def request_health():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/api/v1/health")

    response = asyncio.run(request_health())

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.1.0"
    assert payload["services"]["llm"] == "unconfigured"
    assert "api_key" not in response.text.lower()

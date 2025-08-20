import asyncio
from httpx import AsyncClient
from app.main import app

def test_health_check():
    async def run():
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}
    asyncio.run(run())

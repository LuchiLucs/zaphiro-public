from core.utils import get_logger
import pytest
import asyncio

logger = get_logger("test", "DEBUG")


@pytest.mark.anyio
async def test_async_report_generation_e2e(client):
    # Login to get the token
    login_data = {
        "username": "manager",
        "password": "manager",
        "scope": "manager"
    }
    
    login_response = await client.post("auth/token", data=login_data)
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Trigger
    payload = {"start_date": "2026-01-01T00:00:00Z", "end_date": "2026-01-30T00:00:00Z"}
    response = await client.post("/reports", json=payload, headers=headers)
    assert response.status_code == 202
    report_id = response.json()["id"]

    # Poll with enough time
    max_attempts = 10
    completed = False

    for _ in range(max_attempts):
        print("Calling get report...")
        status_res = await client.get(f"/reports/{report_id}", headers=headers)

        if status_res.status_code == 200:
            data = status_res.json()
            if data.get("status") == "completed":
                completed = True
                break

        await asyncio.sleep(0.5)

    assert completed is True, "Report timed out"

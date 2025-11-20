import asyncio
import os
from typing import Tuple
import httpx
import pytest

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_USER_TOKEN = os.getenv("TEST_USER_TOKEN")
TEST_TRIP_ID = os.getenv("TEST_TRIP_ID")
TEST_SEAT_NUMBER = os.getenv("TEST_SEAT_NUMBER")
PARALLEL_REQUESTS = int(os.getenv("TEST_CONCURRENT_REQUESTS", "2"))


async def _try_reserve() -> Tuple[int, dict]:
    payload = {
        "trip_id": int(TEST_TRIP_ID),
        "seat_number": int(TEST_SEAT_NUMBER)
    }
    headers = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10) as client:
        response = await client.post("/v1/booking/reserve", json=payload, headers=headers)
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}
        return response.status_code, body


@pytest.mark.asyncio
async def test_concurrent_reservation_same_seat():
    """
    Ensures Redis seat locks work: exactly one request should succeed,
    the rest should return conflict (409) when hitting the same seat simultaneously.
    """
    if not all([TEST_USER_TOKEN, TEST_TRIP_ID, TEST_SEAT_NUMBER]):
        pytest.skip("Set TEST_USER_TOKEN, TEST_TRIP_ID and TEST_SEAT_NUMBER env vars to run this test.")

    tasks = [_try_reserve() for _ in range(max(2, PARALLEL_REQUESTS))]
    results = await asyncio.gather(*tasks)

    successes = [res for res in results if res[0] in (200, 201)]
    conflicts = [res for res in results if res[0] in (400, 409)]

    assert len(successes) == 1, f"Expected exactly one success, got: {results}"
    assert len(conflicts) == len(results) - 1, f"Expected remaining requests to conflict, got: {results}"
import asyncio
import httpx

async def reserve():
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOTExMTIzNDU2NyIsImV4cCI6MTc2NDE0ODMxOH0.JeHyjjoaNgtnYCYQHG39nacasXnUHJXeEYcFvlHZQ94"}
        r = await client.post("http://localhost:8000/v1/booking/reserve", json={"trip_id": 1, "seat_number": 10}, headers=headers)
        print(r.status_code, r.json())

async def main():
    tasks = [reserve() for _ in range(100)]
    await asyncio.gather(*tasks)

asyncio.run(main())
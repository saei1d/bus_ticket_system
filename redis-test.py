# redis_test.py
import asyncio
from app.core.redis import redis_client as redis

async def test_redis():
    try:
        pong = await redis.ping()
        print("Redis متصل است:", pong)
        
        # تست ساده
        await redis.set("test_key", "سلام سعید شجاعی!")
        value = await redis.get("test_key")
        print("مقدار ذخیره شده:", value)
        
    except Exception as e:
        print("خطا در اتصال Redis:", e)

if __name__ == "__main__":
    asyncio.run(test_redis())
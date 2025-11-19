# راهنمای استفاده از Alembic در Docker

این راهنما به شما نشان می‌دهد چطور migration‌های Alembic را در Docker اجرا کنید.

## روش 1: اجرای دستی Migration (پیشنهادی)

### مرحله 1: ساخت و راه‌اندازی کانتینرها

```bash
# ساخت و راه‌اندازی تمام سرویس‌ها
docker-compose up -d --build
```

### مرحله 2: بررسی وضعیت کانتینرها

```bash
# بررسی اینکه همه کانتینرها در حال اجرا هستند
docker-compose ps
```

### مرحله 3: اجرای Migration

```bash
# اجرای migration در کانتینر API
docker exec -it bus_ticket_api alembic upgrade head
```

### مرحله 4: بررسی وضعیت Migration

```bash
# مشاهده وضعیت فعلی migration
docker exec -it bus_ticket_api alembic current

# مشاهده تاریخچه migration‌ها
docker exec -it bus_ticket_api alembic history
```

---

## روش 2: ساخت Migration جدید

اگر می‌خواهید یک migration جدید بسازید:

```bash
# ساخت migration جدید (autogenerate)
docker exec -it bus_ticket_api alembic revision --autogenerate -m "توضیحات تغییرات"

# یا ساخت migration خالی
docker exec -it bus_ticket_api alembic revision -m "توضیحات تغییرات"
```

---

## روش 3: Rollback Migration

اگر می‌خواهید migration را برگردانید:

```bash
# برگرداندن یک migration
docker exec -it bus_ticket_api alembic downgrade -1

# برگرداندن به یک revision خاص
docker exec -it bus_ticket_api alembic downgrade <revision_id>
```

---

## روش 4: اجرای خودکار Migration در Startup (اختیاری)

اگر می‌خواهید migration‌ها به صورت خودکار در startup اجرا شوند، می‌توانید `app/main.py` را تغییر دهید:

```python
@app.on_event("startup")
async def startup_event():
    import subprocess
    subprocess.run(["alembic", "upgrade", "head"])
    print("Migrations completed!")
```

**نکته:** این روش پیشنهاد نمی‌شود چون در صورت خطا، API راه‌اندازی نمی‌شود.

---

## دستورات مفید دیگر

### مشاهده لاگ‌های Migration

```bash
docker logs bus_ticket_api | grep -i alembic
```

### اتصال مستقیم به دیتابیس

```bash
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db
```

### بررسی جدول‌های ساخته شده

```bash
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db -c "\dt"
```

### بررسی جدول alembic_version

```bash
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db -c "SELECT * FROM alembic_version;"
```

---

## مراحل کامل Setup (از صفر)

```bash
# 1. ساخت و راه‌اندازی
docker-compose up -d --build

# 2. صبر کنید تا PostgreSQL آماده شود (حدود 10 ثانیه)
sleep 10

# 3. اجرای migration
docker exec -it bus_ticket_api alembic upgrade head

# 4. اجرای seeder (ساخت داده‌های اولیه)
docker exec -it bus_ticket_api python seeders/complete_seeder.py

# 5. ساخت 100,000 رزرو (اختیاری)
docker exec -it bus_ticket_api python -c "
import asyncio, sys
sys.path.append('/app')
from seeders.heavy_booking_seeder import create_100k_bookings
asyncio.run(create_100k_bookings())
"

# 6. بررسی تعداد رزروها
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db -c "SELECT COUNT(*) FROM bookings;"
```

---

## عیب‌یابی

### مشکل: "alembic: command not found"

**راه حل:** مطمئن شوید که `alembic` در `requirements.txt` اضافه شده و کانتینر rebuild شده:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### مشکل: "Can't locate revision identified by 'xxxxx'"

**راه حل:** migration files در پوشه `migrations/versions/` باید در کانتینر موجود باشند. مطمئن شوید که volume mount درست است.

### مشکل: "Target database is not up to date"

**راه حل:** migration‌های pending را اجرا کنید:

```bash
docker exec -it bus_ticket_api alembic upgrade head
```

---

## نکات مهم

1. ✅ همیشه قبل از migration، از دیتابیس backup بگیرید
2. ✅ migration‌ها را در محیط development تست کنید
3. ✅ migration files را در Git commit کنید
4. ✅ از `--autogenerate` با احتیاط استفاده کنید و همیشه migration را بررسی کنید
5. ✅ در production، migration را به صورت دستی اجرا کنید


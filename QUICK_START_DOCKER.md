# راهنمای سریع: استفاده از Alembic در Docker

## 🚀 مراحل ساده (فقط Docker)

### مرحله 1: ساخت و راه‌اندازی کانتینرها

```bash
docker-compose up -d --build
```

این دستور:
- PostgreSQL را راه‌اندازی می‌کند
- Redis را راه‌اندازی می‌کند  
- API را build و راه‌اندازی می‌کند

**صبر کنید تا همه کانتینرها ready شوند (حدود 10-15 ثانیه)**

---

### مرحله 2: بررسی وضعیت

```bash
docker-compose ps
```

باید همه سرویس‌ها `Up` باشند.

---

### مرحله 3: ساخت اولین Migration (فقط یک بار)

اگر هنوز migration ندارید، باید یک migration اولیه بسازید:

```bash
docker exec -it bus_ticket_api alembic revision --autogenerate -m "initial migration"
```

این دستور:
- تمام مدل‌های شما را بررسی می‌کند
- یک migration file می‌سازد که تمام جدول‌ها را ایجاد می‌کند

---

### مرحله 4: اجرای Migration

```bash
docker exec -it bus_ticket_api alembic upgrade head
```

این دستور:
- تمام migration‌های pending را اجرا می‌کند
- جدول‌ها را در دیتابیس می‌سازد

**خروجی موفق:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, initial migration
```

---

### مرحله 5: اجرای Seeder (ساخت داده‌های اولیه)

```bash
docker exec -it bus_ticket_api python seeders/complete_seeder.py
```

این دستور:
- کاربران را می‌سازد
- مسیرها را می‌سازد
- اتوبوس‌ها را می‌سازد
- سفرها را می‌سازد
- صندلی‌ها را می‌سازد

---

### مرحله 6: ساخت 100,000 رزرو (اختیاری)

```bash
docker exec -it bus_ticket_api python -c "
import asyncio, sys
sys.path.append('/app')
from seeders.heavy_booking_seeder import create_100k_bookings
asyncio.run(create_100k_bookings())
"
```

**نکته:** این ممکن است چند دقیقه طول بکشد.

---

### مرحله 7: بررسی نتیجه

```bash
# بررسی تعداد رزروها
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db -c "SELECT COUNT(*) FROM bookings;"

# بررسی جدول‌ها
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db -c "\dt"
```

---

## 📝 دستورات مفید

### مشاهده وضعیت Migration

```bash
docker exec -it bus_ticket_api alembic current
```

### مشاهده تاریخچه Migration‌ها

```bash
docker exec -it bus_ticket_api alembic history
```

### ساخت Migration جدید (بعد از تغییر مدل)

```bash
docker exec -it bus_ticket_api alembic revision --autogenerate -m "توضیحات تغییرات"
```

### Rollback (برگرداندن یک Migration)

```bash
docker exec -it bus_ticket_api alembic downgrade -1
```

---

## 🔄 اگر می‌خواهید از اول شروع کنید

```bash
# 1. توقف و حذف همه چیز
docker-compose down -v

# 2. راه‌اندازی مجدد
docker-compose up -d --build

# 3. صبر کنید
sleep 10

# 4. ساخت و اجرای migration
docker exec -it bus_ticket_api alembic revision --autogenerate -m "initial migration"
docker exec -it bus_ticket_api alembic upgrade head

# 5. اجرای seeder
docker exec -it bus_ticket_api python seeders/complete_seeder.py
```

---

## ❓ سوالات متداول

### Q: چرا باید از Alembic استفاده کنم؟

**A:** Alembic به شما امکان می‌دهد:
- تغییرات دیتابیس را version control کنید
- migration‌ها را در تیم share کنید
- به راحتی rollback کنید
- در production به صورت کنترل شده migration اجرا کنید

### Q: آیا می‌توانم از `Base.metadata.create_all()` استفاده کنم؟

**A:** بله، اما فقط برای development. در production باید از Alembic استفاده کنید.

### Q: اگر migration خطا داد چه کنم؟

**A:** 
1. لاگ‌ها را بررسی کنید: `docker logs bus_ticket_api`
2. وضعیت migration را ببینید: `docker exec -it bus_ticket_api alembic current`
3. اگر نیاز بود rollback کنید: `docker exec -it bus_ticket_api alembic downgrade -1`

---

## ✅ چک‌لیست نهایی

- [ ] کانتینرها در حال اجرا هستند
- [ ] Migration اجرا شده است
- [ ] Seeder اجرا شده است
- [ ] API در `http://localhost:8000` در دسترس است
- [ ] می‌توانید با Postman تست کنید

---

**🎉 تمام! حالا پروژه شما آماده است.**


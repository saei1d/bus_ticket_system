
```bash
git clone https://github.com/yourusername/iran-bus-ticket-system.git
cd iran-bus-ticket-system
docker-compose up -d --build




docker-compose down -v
docker-compose up -d --build
docker-compose down --remove-orphans



Name: Bus Ticket DB
tab Connection:
Host name/address: bus_ticket_postgres 
Port: 5432
Maintenance database: bus_ticket_db
Username: postgres
Password: postgres



# ۱. اجرای migration (ساخت جدول‌ها)
docker exec -it bus_ticket_api alembic revision --autogenerate -m "initial migration"
docker exec -it bus_ticket_api alembic upgrade head

# ۲. seeder کامل (کاربر + ۵۰۰۰ سفر + ۱۵۰٬۰۰۰ صندلی)
docker exec -it bus_ticket_api python seeders/complete_seeder.py

# ۳. ساخت ۱۰۰٬۰۰۰ رزرو
docker exec -it bus_ticket_api python -c "
import asyncio, sys
sys.path.append('/app')
from seeders.heavy_booking_seeder import create_100k_bookings
asyncio.run(create_100k_bookings())
"

# ۴. چک کردن تعداد رزروها
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db -c "SELECT COUNT(*) FROM bookings;"
```

## استفاده از Postman Collection

1. فایل `postman_collection/Bus_Ticket_System.postman_collection.json` را در Postman import کنید
2. متغیر `base_url` را به آدرس سرور خود تنظیم کنید (پیش‌فرض: `http://localhost:8000`)
3. ابتدا endpoint "Login" را اجرا کنید تا token دریافت کنید (به صورت خودکار در collection variable ذخیره می‌شود)
4. سایر endpoint‌ها را تست کنید

## Database Migrations

برای استفاده از Alembic migrations در Docker:

```bash
# ساخت migration جدید
docker exec -it bus_ticket_api alembic revision --autogenerate -m "description"

# اعمال migrations
docker exec -it bus_ticket_api alembic upgrade head

# rollback
docker exec -it bus_ticket_api alembic downgrade -1

# مشاهده وضعیت فعلی
docker exec -it bus_ticket_api alembic current
```

**📖 راهنمای کامل:** فایل `QUICK_START_DOCKER.md` را برای راهنمای مرحله به مرحله مطالعه کنید.

## API Endpoints

### Authentication
- `POST /v1/auth/register` - ثبت‌نام کاربر جدید
- `POST /v1/auth/login` - ورود و دریافت token

### Trips
- `GET /v1/trips/available` - دریافت لیست سفرهای موجود
  - Query params: `origin`, `destination`, `sort` (cheapest/expensive)

### Booking
- `POST /v1/booking/reserve` - رزرو صندلی (نیاز به authentication)
- `GET /v1/booking/my-bookings` - لیست بلیط‌های من (نیاز به authentication)
- `POST /v1/booking/cancel/{booking_id}` - لغو بلیط (نیاز به authentication)

### Admin
- `POST /v1/admin/bus` - ایجاد اتوبوس جدید (نیاز به admin role)
- `GET /v1/admin/buses` - لیست تمام اتوبوس‌ها (نیاز به admin role)
- `POST /v1/admin/trip` - ایجاد سفر جدید (نیاز به admin role)
- `POST /v1/admin/wallet/charge` - شارژ کیف پول کاربر (نیاز به admin role)

### Reports (Admin Only)
- `GET /v1/admin/reports/hourly-success-bookings` - تعداد رزروهای موفق در هر ساعت
- `GET /v1/admin/reports/bus-monthly-income` - درآمد و تعداد رزرو هر اتوبوس در هر ماه
- `GET /v1/admin/reports/top-driver` - فعال‌ترین (پرکارترین) اتوبوس


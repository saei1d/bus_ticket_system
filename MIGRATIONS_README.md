# Database Migrations Guide

این پروژه از Alembic برای مدیریت migration‌های دیتابیس استفاده می‌کند.

## نصب Alembic

```bash
pip install -r requirements.txt
```

## ساخت Migration جدید

برای ساخت یک migration جدید بر اساس تغییرات مدل‌ها:

```bash
alembic revision --autogenerate -m "description of changes"
```

## اعمال Migration‌ها

برای اعمال تمام migration‌های pending:

```bash
alembic upgrade head
```

برای اعمال migration به یک revision خاص:

```bash
alembic upgrade <revision_id>
```

## Rollback Migration

برای rollback یک migration:

```bash
alembic downgrade -1
```

برای rollback به یک revision خاص:

```bash
alembic downgrade <revision_id>
```

## مشاهده تاریخچه Migration‌ها

```bash
alembic history
```

## مشاهده وضعیت فعلی

```bash
alembic current
```

## نکات مهم

- قبل از ساخت migration جدید، مطمئن شوید که تمام مدل‌ها در `app/models/__init__.py` import شده‌اند
- Migration files در پوشه `migrations/versions/` ذخیره می‌شوند
- همیشه migration‌ها را قبل از commit تست کنید


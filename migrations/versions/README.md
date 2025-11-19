# Migration Files

This directory contains Alembic migration files.

To create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:
```bash
alembic upgrade head
```

To rollback:
```bash
alembic downgrade -1
```


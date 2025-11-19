# Bus Ticket Reservation System

A professional bus ticket reservation system built with FastAPI, PostgreSQL, and Redis. This system provides secure, concurrent-safe booking with rate limiting, distributed locking, and comprehensive admin features.

## Features

- ✅ **FastAPI + asyncpg + PostgreSQL** - Fully async and optimized
- ✅ **Redis Integration** - Cache, rate limiting, and distributed locking
- ✅ **Security** - JWT authentication, role-based access control
- ✅ **Rate Limiting** - 20 bookings per day per user, 10 requests/minute for auth
- ✅ **Concurrency Safety** - Redis distributed locks prevent race conditions
- ✅ **Admin Panel** - Bus and trip management, wallet charging, reports
- ✅ **Comprehensive Reports** - Hourly bookings, monthly income, busiest bus
- ✅ **Database Migrations** - Alembic for version control
- ✅ **100,000+ Test Records** - Ready for performance testing

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Step 1: Clone and Start

```bash
git clone <repository-url>
cd bus_ticket_system
docker-compose up -d --build
```

Wait 10-15 seconds for all services to start.

### Step 2: Run Database Migrations

```bash
# Create initial migration
docker exec -it bus_ticket_api alembic revision --autogenerate -m "initial migration"

# Apply migrations
docker exec -it bus_ticket_api alembic upgrade head
```

### Step 3: Seed Database

```bash
# Create users, routes, buses, trips, and seats (150,000 seats)
docker exec -it bus_ticket_api python seeders/complete_seeder.py

# Create 100,000 bookings (optional, takes a few minutes)
docker exec -it bus_ticket_api python -c "
import asyncio, sys
sys.path.append('/app')
from seeders.heavy_booking_seeder import create_100k_bookings
asyncio.run(create_100k_bookings())
"
```

### Step 4: Verify Setup

```bash
# Check booking count
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db -c "SELECT COUNT(*) FROM bookings;"
```

## Using Postman Collection

1. Import `postman_collection/Bus_Ticket_System.postman_collection.json` into Postman
2. Set `base_url` variable to `http://localhost:8000` (or your server URL)
3. Run "Login" endpoint first - token will be automatically saved
4. Test other endpoints

## API Endpoints

### Authentication

- **POST** `/v1/auth/register` - Register new user
  - Body: `{"mobile": "09123456789", "password": "123456", "role": "passenger"}`
  - Rate limit: 10 requests/minute per IP and phone

- **POST** `/v1/auth/login` - Login and get JWT token
  - Body: `{"mobile": "09123456789", "password": "123456"}`
  - Returns: `{"access_token": "...", "token_type": "bearer"}`
  - Rate limit: 10 requests/minute per IP and phone

### Trips

- **GET** `/v1/trips/available` - Get available trips
  - Query params:
    - `origin` (optional) - Filter by origin city
    - `destination` (optional) - Filter by destination city
    - `sort` (optional) - `cheapest` or `expensive` (default: cheapest)
  - Example: `/v1/trips/available?origin=Tehran&destination=Mashhad&sort=cheapest`
  - Cached for 60 seconds

### Booking

- **POST** `/v1/booking/reserve` - Reserve a seat (requires authentication)
  - Headers: `Authorization: Bearer <token>`
  - Body: `{"trip_id": 1, "seat_number": 5}`
  - Rate limit: 20 bookings per day per user
  - Returns: Booking details with booking_id

- **GET** `/v1/booking/my-bookings` - Get user's booking history (requires authentication)
  - Headers: `Authorization: Bearer <token>`
  - Returns: List of all user's bookings

- **POST** `/v1/booking/cancel/{booking_id}` - Cancel a booking (requires authentication)
  - Headers: `Authorization: Bearer <token>`
  - Only allowed before departure time
  - Refund processed in background
  - Security: Users can only cancel their own bookings

### Admin Endpoints

All admin endpoints require admin role and authentication.

- **POST** `/v1/admin/bus` - Create new bus
  - Body: `{"plate_number": "IR12A345", "capacity": 44, "is_vip": false}`

- **GET** `/v1/admin/buses` - List all buses

- **POST** `/v1/admin/trip` - Create new trip (automatically creates seats)
  - Body: `{"route_id": 1, "bus_id": 1, "departure_time": "2025-12-01T10:00:00Z", "arrival_time": "2025-12-01T18:00:00Z", "price": 1500000}`

- **POST** `/v1/admin/wallet/charge` - Charge user wallet
  - Body: `{"mobile": "09123456789", "amount": 5000000}`

### Reports (Admin Only)

- **GET** `/v1/admin/reports/hourly-success-bookings` - Bookings per hour
  - Query params:
    - `date` (optional) - Filter by date (YYYY-MM-DD format)
    - `hour` (optional) - Filter by hour (0-23)
  - Examples:
    - `/v1/admin/reports/hourly-success-bookings` - All hours
    - `/v1/admin/reports/hourly-success-bookings?date=2025-12-14` - Specific date
    - `/v1/admin/reports/hourly-success-bookings?date=2025-12-14&hour=14` - Specific date and hour

- **GET** `/v1/admin/reports/bus-monthly-income` - Monthly income per bus
  - Returns: Income and booking count per bus per month

- **GET** `/v1/admin/reports/top-driver` - Most active bus
  - Returns: Bus with highest number of bookings

## Database Migrations

### Create New Migration

```bash
docker exec -it bus_ticket_api alembic revision --autogenerate -m "description of changes"
```

### Apply Migrations

```bash
docker exec -it bus_ticket_api alembic upgrade head
```

### Rollback

```bash
docker exec -it bus_ticket_api alembic downgrade -1
```

### Check Status

```bash
docker exec -it bus_ticket_api alembic current
docker exec -it bus_ticket_api alembic history
```

For detailed migration guide, see `MIGRATIONS_README.md` and `QUICK_START_DOCKER.md`.

## Default Admin Account

After running the seeder, you can login with:

- **Mobile**: `09990000001`
- **Password**: `123456`
- **Role**: `admin`

## Project Structure

```
app/
├── api/              # API endpoints (REST)
│   └── v1/
│       └── endpoints/
├── core/             # Core configurations (config, security, dependencies)
├── crud/             # Database operations
├── db/               # Database session and base
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas (DTOs)
├── services/         # Business logic layer
│   ├── booking_queries.py    # SQL queries for bookings
│   ├── admin_queries.py       # SQL queries for admin
│   ├── rate_limit.py          # Rate limiting logic
│   └── ...
└── utils/            # Utility functions
```

## Security Features

- ✅ JWT Authentication with 8-hour token expiry
- ✅ Role-based Access Control (Admin, Operator, Passenger)
- ✅ Rate Limiting:
  - 20 bookings per day per user
  - 10 requests per minute for login/register (per IP and phone)
- ✅ Redis Distributed Lock for concurrent bookings
- ✅ Input Validation with Pydantic
- ✅ SQL Injection Protection (Parameterized Queries)
- ✅ User can only cancel their own bookings

## Important Notes

- Each booking must complete in less than 2 seconds ✅
- Each user can make maximum 20 bookings per day ✅
- Each seat can only be reserved once per trip ✅
- System contains at least 100,000 bookings for testing ✅
- All bookings are concurrency-safe with Redis locks ✅

## Troubleshooting

### Check Container Status

```bash
docker-compose ps
```

### View Logs

```bash
docker logs bus_ticket_api
docker logs bus_ticket_postgres
docker logs bus_ticket_redis
```

### Reset Everything

```bash
docker-compose down -v
docker-compose up -d --build
```

### Access Database Directly

```bash
docker exec -it bus_ticket_postgres psql -U postgres -d bus_ticket_db
```

## Testing

For concurrent testing:

```bash
python test/test_concurrent.py
```

## Documentation

- `QUICK_START_DOCKER.md` - Step-by-step Docker guide
- `DOCKER_MIGRATIONS_GUIDE.md` - Complete migration guide
- `MIGRATIONS_README.md` - Alembic usage guide

## License

This project is developed as a task for Saeid Shojaei.

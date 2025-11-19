# app/services/admin_queries.py
"""
SQL queries for admin operations.
Separated from endpoints for better organization.
"""
from sqlalchemy import text


# Check if bus plate number exists
CHECK_BUS_PLATE = text("SELECT 1 FROM buses WHERE plate_number = :p")


# Create new bus
CREATE_BUS = text("""
    INSERT INTO buses (plate_number, capacity, is_vip)
    VALUES (:p, :c, :v) RETURNING id
""")


# Check if route exists
CHECK_ROUTE = text("SELECT 1 FROM routes WHERE id = :rid")


# Check if bus exists
CHECK_BUS = text("SELECT 1 FROM buses WHERE id = :bid")


# Create new trip
CREATE_TRIP = text("""
    INSERT INTO trips (route_id, bus_id, departure_time, arrival_time, price)
    VALUES (:r, :b, :d, :a, :p) RETURNING id
""")


# Get bus capacity
GET_BUS_CAPACITY = text("SELECT capacity FROM buses WHERE id = :bid")


# Create seat for trip
CREATE_SEAT = text("""
    INSERT INTO seats (trip_id, seat_number, is_reserved)
    VALUES (:tid, :sn, false)
""")


# List all buses
LIST_BUSES = text("SELECT id, plate_number, capacity, is_vip FROM buses ORDER BY id")


# Get user by mobile
GET_USER_BY_MOBILE = text("SELECT id FROM users WHERE mobile = :m")


# Charge wallet
CHARGE_WALLET = text("""
    UPDATE wallets SET balance = balance + :amount 
    WHERE user_id = :uid
""")


# Get wallet balance
GET_WALLET_BALANCE = text("SELECT balance FROM wallets WHERE user_id = :uid")


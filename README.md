# Inventory API

A backend system for an online store that handles **concurrent purchases**, **stock safety**, and **duplicate request prevention** — built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.x |
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Server | Uvicorn |
| Docs | Swagger UI (auto-generated) |

---

##  Problem Statement

An online store where:
- Products have limited stock
- Many users can try to buy the same product at the same time
- The system must **never sell more than available stock**

### The One Rule That Must Never Break
> Stock must **never go below zero** — even if two users click at the same time, the request is sent twice, or the server crashes.

---

## Database Schema

### Tables

#### `products`
Stores each product and its live stock count.

| Column | Type | Description |
|---|---|---|
| sku | VARCHAR (PK) | Unique product code |
| name | VARCHAR | Product name |
| stock | INTEGER | Current stock (≥ 0 enforced by CHECK constraint) |

#### `orders`
One row per order. The unique `idempotency_key` prevents duplicate orders.

| Column | Type | Description |
|---|---|---|
| id | INTEGER (PK) | Auto-incremented order ID |
| idempotency_key | VARCHAR (UNIQUE) | Prevents duplicate order creation |
| status | VARCHAR | Order status (e.g., "confirmed") |
| created_at | DATETIME | Timestamp of creation |

#### `order_items`
Line items belonging to each order. Supports multi-product orders.

| Column | Type | Description |
|---|---|---|
| id | INTEGER (PK) | Auto-incremented |
| order_id | INTEGER (FK → orders) | Which order this item belongs to |
| sku | VARCHAR (FK → products) | Which product was ordered |
| quantity | INTEGER | How many units ordered |

---

## How Safety Is Guaranteed

| Risk | Solution |
|---|---|
| Two users buying last item simultaneously | `SELECT FOR UPDATE` locks the product row — only one transaction proceeds at a time |
| Duplicate/retried requests | `idempotency_key` has a `UNIQUE` constraint — same key returns existing order |
| Stock going negative | DB-level `CHECK (stock >= 0)` constraint + application-level validation |
| Partial order failure | Single `db.commit()` covers order creation + all stock deductions atomically |
| Server crash mid-order | PostgreSQL transaction rollback ensures no partial state is saved |

---

## API Endpoints

### `POST /products`
Create a new product with stock.

**Request:**
```json
{
  "sku": "SKU-1",
  "name": "Blue T-Shirt",
  "stock": 10
}
```

**Response:**
```json
{
  "sku": "SKU-1",
  "name": "Blue T-Shirt",
  "stock": 10
}
```

---

### `GET /products/{sku}`
Get a product and its current stock.

**Response:**
```json
{
  "sku": "SKU-1",
  "name": "Blue T-Shirt",
  "stock": 8
}
```

---

### `POST /orders`
Place an order. Handles concurrency and idempotency.

**Request:**
```json
{
  "idempotency_key": "order-abc-001",
  "items": [
    { "sku": "SKU-1", "quantity": 2 }
  ]
}
```

**Response (success):**
```json
{
  "id": 1,
  "idempotency_key": "order-abc-001",
  "status": "confirmed",
  "created_at": "2026-04-16T10:00:00",
  "items": [
    { "sku": "SKU-1", "quantity": 2 }
  ]
}
```

**Response (insufficient stock):**
```json
{
  "detail": "Insufficient stock for SKU-1. Available: 1"
}
```

---

### `GET /orders/{id}`
Retrieve an order by its ID.

**Response:**
```json
{
  "id": 1,
  "idempotency_key": "order-abc-001",
  "status": "confirmed",
  "created_at": "2026-04-16T10:00:00",
  "items": [
    { "sku": "SKU-1", "quantity": 2 }
  ]
}
```

---

## Local Setup (Windows PowerShell)

### 1. Clone the repository
```powershell
git clone https://github.com/sivap365/INVENTORY-API.git
cd INVENTORY-API
```

### 2. Create and activate virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
pip install fastapi uvicorn psycopg2-binary sqlalchemy python-dotenv
```

### 4. Set up PostgreSQL
Create the database:
```sql
CREATE DATABASE inventory_db;
```

### 5. Create `.env` file
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/inventory_db
```

### 6. Run the server
```powershell
uvicorn main:app --reload
```

### 7. Add stock safety constraint (run once after first startup)
```sql
ALTER TABLE products ADD CONSTRAINT stock_non_negative CHECK (stock >= 0);
```

### 8. Open API docs
```
http://127.0.0.1:8000/docs
```

---

## Project Structure

```
inventory-api/
├── .env                  # DB credentials (not committed)
├── main.py               # App entry point
├── database.py           # DB connection and session
├── models.py             # SQLAlchemy table definitions
├── schemas.py            # Pydantic request/response models
└── routers/
    ├── products.py       # POST /products, GET /products/{sku}
    └── orders.py         # POST /orders, GET /orders/{id}
```

# Internal Wallet Service

> A high-performance, double-entry ledger wallet service built with FastAPI, PostgreSQL, and SQLAlchemy (Async).

This service implements a robust internal wallet system capable of handling concurrent transactions with strict consistency and auditability. It leverages double-entry bookkeeping principles to ensure that every debit has a corresponding credit, maintaining a zero-sum balance across all transaction entries.

---

## 🚀 Features

- **Double-Entry Ledger core**: Every transaction is recorded as multiple postings that must sum to zero, ensuring complete financial integrity.
- **ACID Compliant**: Transactions are atomic and consistent, backed by PostgreSQL's strong consistency guarantees.
- **Concurrency Control**: Utilizes row-level locking (`SELECT ... FOR UPDATE`) to prevent race conditions and double-spending, even under high load.
- **Idempotency**: Prevents duplicate processing of the same request using unique `reference_id` keys.
- **Audit Trail**: Full history of all transactions and postings for auditing and reconciliation.
- **Containerized**: Ready-to-deploy Docker environment with automated database migrations and seeding.

## 🛠 Tech Stack

- **Language**: Python 3.11
- **Framework**: FastAPI (High performance, easy to use)
- **Database**: PostgreSQL 15 (Relational, robust)
- **ORM**: SQLAlchemy (Async) + Alembic (Migrations)
- **Validation**: Pydantic
- **Testing**: Pytest

---

## 🏁 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)

### 🐳 Fast Start (Docker)

The easiest way to run the application is using Docker Compose.

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <dino_ventures>
   ```

2. **Start the services:**
   ```bash
   docker compose up --build
   ```
   This command will:
   - Start the PostgreSQL database container.
   - Build the application image.
   - Wait for the database to be ready.
   - Run database migrations (`alembic upgrade head`).
   - Seed the database with initial accounts and funds.
   - Start the API server on `http://localhost:8000`.

3. **Verify it's running:**
   Visit [http://localhost:8000/docs](http://localhost:8000/docs) to see the interactive API documentation.

### 💻 Local Development

If you prefer to run the application locally without Docker for development:

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database:**
   Ensure you have a PostgreSQL instance running. Update the `.env` file or environment variables to point to your database.
   ```bash
   # Example .env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/wallet_db
   ```

4. **Run migrations and seed:**
   ```bash
   alembic upgrade head
   python seed.py
   ```

5. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 📚 API Documentation

The API is documented using OpenAPI (Swagger). Once the app is running, navigate to `/docs` for the interactive UI.

### Key Endpoints

#### 1. Check Balance
Retrieves the current balance and account details for a user.

- **GET** `/wallet/{user_id}/balance`
- **Response**:
  ```json
  {
    "user_id": 2,
    "total_balance": 100,
    "accounts": [
      {
        "id": 3,
        "name": "Alice's Wallet",
        "currency": "GOLD",
        "balance": 100
      }
    ]
  }
  ```

#### 2. Top Up Wallet
Adds funds to a user's wallet from the system Treasury.

- **POST** `/wallet/topup`
- **Body**:
  ```json
  {
    "user_id": 2,
    "amount": 100,
    "reference_id": "unique-ref-001",
    "description": "Weekly Allowance"
  }
  ```

#### 3. Spend Credits
Deducts funds from a user's wallet, transferring them to the Treasury.

- **POST** `/wallet/spend`
- **Body**:
  ```json
  {
    "user_id": 2,
    "amount": 50,
    "reference_id": "unique-ref-002",
    "description": "Purchase Item #123"
  }
  ```

---

## 🧪 Testing & Verification

### automated Verification Script

A script is included to verify the core transaction flows (Top-up -> Bonus -> Spend -> Balance Check).

Run it using the provided helper script (requires Docker):

```bash
./run_verification.sh
```

Or manually against a running server:

```bash
# Ensure you have 'requests' installed
pip install requests

python verification_script.py
```

### Running Unit Tests

(If applicable, add instructions for running `pytest` here)
```bash
pytest
```

---

## 🏗 Architecture & Design Decisions

### Double-Entry Bookkeeping
We chose a double-entry system to ensure financial accuracy. Every transaction involves at least two accounts: a **Source** and a **Destination**.
- **User Top-Up**: Credit User Wallet (+), Debit Treasury (-).
- **User Spend**: Debit User Wallet (-), Credit Treasury (+).

The sum of all postings in a single transaction block is always exactly `0`.

### Pessimistic Locking
To handle concurrent requests safely, we use **Pessimistic Locking** (`SELECT ... FOR UPDATE`). When a transaction is processed:
1. We sort the account IDs involved (to prevent deadlocks).
2. We lock the rows for these accounts in the database.
3. We read the latest balance, validate checks (e.g., sufficient funds), and update the balance.
4. The lock is released only when the transaction commits.

This ensures that if two requests try to spend from the same wallet simultaneously, they are serialized, preventing the balance from going negative or being updated incorrectly.

### Service Layer Pattern
Business logic is encapsulated in `app/services/ledger.py`. The API routers (`app/routers/`) are thin wrappers that handle HTTP requests and delegate complex logic to the service layer. This encourages code reuse and makes testing easier.

# Expense Tracker — FastAPI Backend

A production-grade, Clean Architecture REST API built with FastAPI, SQLAlchemy 2.0, Alembic, and PostgreSQL/SQLite.

## 1. Architecture

```text
API / Presentation (FastAPI Routes, Pydantic Schemas, Middlewares)
       ↓
Application Layer (Use Cases: Auth, Expenses, Reports, Exports, Profile)
       ↓
Domain Layer (Entities, Value Objects, Repository Interfaces, Services)
       ↑
Infrastructure Layer (SQLAlchemy 2.0 Repositories, Models, Migrations, Security)
```

The domain contracts are completely decoupled from SQLAlchemy and web frameworks, ensuring a frictionless migration path to Java/Spring Boot or MongoDB whenever needed.

## 2. Features

- **Authentication & Security**: Access tokens (JWT), refresh tokens, password hashing with bcrypt, strict account ownership validation.
- **Expense CRUD**: Full CRUD with Decimal precision (`NUMERIC(14, 2)`), date filtering, search, and pagination.
- **Dashboard & Aggregated Reports**: Balance calculations, today/month totals, daily totals, monthly breakdown, yearly comparisons, and category percentage distributions.
- **Excel Export**: On-demand generation of multi-sheet styled `.xlsx` workbooks (`Expenses` & `Category Breakdown`) using `openpyxl`.
- **User Settings**: Real-time theme mode (light/dark/system), dynamic theme accent color, multi-currency support, and opening balance management.
- **Traceability**: Unified request tracing with `X-Request-ID` and standardized RFC-compliant error responses.

## 3. Running Locally

### Prerequisites
- Python 3.9+
- Virtual environment

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Dev reads backend/.env.dev (currency, database, JWT, and the other defaults)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Staging reads backend/.env.staging. Real secrets must be set in the host or in .env.
APP_ENV=staging uvicorn app.main:app --host 0.0.0.0 --port 8000

# Prod reads backend/.env.prod. Host env vars override the placeholders.
APP_ENV=prod uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Interactive documentation is available at `http://localhost:8000/docs`.

## 4. Running Tests

```bash
pytest -v
```

## 5. Deployment on Render & Supabase

1. **Supabase Database**: Create a free PostgreSQL project and copy the `Connection String (URI)`.
2. **Render Web Service**:
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt && alembic upgrade head`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Set `APP_ENV=prod` so the service reads `backend/.env.prod`
   - Override the placeholders with real environment variables:
     - `DATABASE_URL`: Your Supabase connection string (`postgresql+psycopg2://...`)
     - `JWT_SECRET`: Random 32-byte hex string
     - `JWT_REFRESH_SECRET`: Random 32-byte hex string
     - `CORS_ORIGINS`: Your Flutter Web Firebase Hosting URL
     - `DEFAULT_CURRENCY`: Currency for new users, for example `INR`

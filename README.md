# Employee Management API

A Flask-based REST API application for managing employees, projects, tickets, logwork tracking, and KPI/formula calculations with JWT authentication, built with SQLAlchemy ORM and PostgreSQL database.

## Project Overview

This project implements a modern web application architecture with separation of concerns:
- **Routes**: HTTP endpoint handlers
- **Services**: Business logic layer
- **DAO**: Data access objects for database operations
- **Models**: SQLAlchemy database models
- **Requests/Responses**: Request validation and response formatting
- **Utils**: Shared helpers (auth, decorators, math engine, number parsing)
- **Validator**: Input validation utilities
- **Configuration**: Environment-based configuration management

## Project Structure

```
.
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory and blueprint registration
│   ├── config.py                # Configuration management
│   ├── dao/                     # Data access objects
│   │   ├── bank_dao.py
│   │   ├── employee_dao.py
│   │   ├── formula_dao.py
│   │   ├── logwork_dao.py
│   │   ├── project_dao.py
│   │   ├── role_dao.py
│   │   ├── ticket_dao.py
│   │   ├── ticket_status_dao.py
│   │   └── ticket_type_dao.py
│   ├── exceptions/              # Custom exception handlers
│   │   ├── handlers.py
│   │   └── http_exceptions.py
│   ├── models/                  # SQLAlchemy models
│   │   ├── bank.py
│   │   ├── employee.py
│   │   ├── logwork.py
│   │   ├── project.py
│   │   ├── project_emp.py
│   │   ├── role.py
│   │   ├── systemparam.py
│   │   ├── ticket.py
│   │   ├── ticket_status.py
│   │   └── ticket_type.py
│   ├── requests/                # Request validation classes
│   │   ├── auth_request.py
│   │   ├── bank_request.py
│   │   ├── employee_request.py
│   │   ├── logwork_request.py
│   │   ├── project_request.py
│   │   └── ticket_request.py
│   ├── responses/               # Response formatting
│   │   └── api_response.py
│   ├── routes/                  # API endpoint handlers
│   │   ├── auth_router.py
│   │   ├── bank_router.py
│   │   ├── employee_router.py
│   │   ├── export_router.py
│   │   ├── formula_router.py
│   │   ├── logwork_router.py
│   │   ├── project_router.py
│   │   ├── role_router.py
│   │   ├── ticket_router.py
│   │   ├── ticket_status_router.py
│   │   └── ticket_type_router.py
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py
│   │   ├── bank_service.py
│   │   ├── employee_service.py
│   │   ├── export_service.py
│   │   ├── formula_service.py
│   │   ├── logwork_service.py
│   │   ├── project_service.py
│   │   ├── role_service.py
│   │   ├── ticket_service.py
│   │   ├── ticket_status_service.py
│   │   └── ticket_type_service.py
│   ├── utils/                   # Helper functions
│   │   ├── auth_helpers.py      # JWT identity resolution, password verification
│   │   ├── decorators.py        # @admin_required decorator
│   │   ├── math_engine.py       # Formula parser and evaluator
│   │   ├── number_parser.py     # Numeric string normalization
│   │   ├── query_helpers.py     # Query parameter parsing utilities
│   │   └── round_float.py       # Recursive float rounding for API payloads
│   └── validator/
│       └── time_validator.py    # Date parsing (DD/MM/YYYY, ISO, datetime)
├── migrations/                  # Alembic database migrations
│   ├── versions/                # Migration scripts
│   ├── env.py                   # Migration environment configuration
│   ├── alembic.ini              # Alembic configuration
│   └── script.py.mako           # Migration template
├── logs/                        # Application log files
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker container configuration
├── docker-compose.yml           # Docker Compose setup
├── Jenkinsfile                  # CI/CD pipeline
└── README.md                    # This file
```

## Architecture

### Layered Architecture

```
Request → Routes → Services → DAO → Database
                      ↕
               Request Validators
```

Each layer has clear responsibilities:

| Layer | Location | Responsibility |
|-------|----------|---------------|
| Routes | `app/routes/` | HTTP handling, request parsing, response formatting |
| Services | `app/services/` | Business logic, validation, orchestration |
| DAO | `app/dao/` | Database queries and mutations |
| Models | `app/models/` | SQLAlchemy table definitions and relationships |
| Requests | `app/requests/` | Input validation and deserialization |
| Responses | `app/responses/` | Standardized API response structure |

## API Endpoints

Base URL: `/api`

### Authentication (`/api/auth`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/auth/login` | Public | Authenticate with email and password |
| GET | `/auth/me` | JWT | Get current authenticated user |
| POST | `/auth/update-password` | JWT | Change own password |
| POST | `/auth/reset-password` | Admin | Reset employee password to their email |

### Employees (`/api/employees`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/employees` | JWT | List employees with pagination, search, sort |
| GET | `/employees/me` | JWT | Get current user profile |
| PUT | `/employees/me` | JWT | Update current user profile |
| GET | `/employees/me/projects` | JWT | Get current user with project allocations |
| GET | `/employees/members/projects` | Admin | List all members with project allocations |
| GET | `/employees/<id>` | JWT | Get employee by UUID or employeeId |
| POST | `/employees` | Admin | Create new employee |
| PUT | `/employees/<id>` | JWT | Update employee by ID |
| DELETE | `/employees/<id>` | Admin | Delete employee (requires `confirm: true`) |
| POST | `/employees/reset-password` | Admin | Reset target employee password |
| PATCH | `/employees/<id>/toggle-status` | Admin | Toggle employee active/inactive |
| PATCH | `/employees/<id>/status` | Admin | Set employee status explicitly |

### Projects (`/api/projects`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/projects` | JWT | List projects with pagination, bank filter, search |
| GET | `/projects/<id>` | JWT | Get project by UUID (optional `include_members`) |
| POST | `/projects` | Admin | Create project |
| PUT | `/projects/<id>` | Admin | Update project |
| POST | `/projects/<id>/members` | Admin | Add or update project members |
| DELETE | `/projects/<id>/members` | Admin | Remove project members |

### Banks (`/api/banks`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/banks` | JWT | List banks with optional pagination/filter/sort |
| GET | `/banks/<id>` | JWT | Get bank by UUID (optional `include_projects`) |
| POST | `/banks` | Admin | Create bank |
| PUT | `/banks/<id>` | Admin | Update bank |
| DELETE | `/banks/<id>` | Admin | Delete bank |

### Logwork (`/api/logworks`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/logworks` | JWT | Get current user's logwork entries |
| GET | `/logworks/admin/all` | Admin | Get all users' logwork with filters |
| GET | `/logworks/<id>` | JWT | Get single logwork (admin or owner) |
| POST | `/logworks` | Admin | Bulk upsert logwork rows |
| DELETE | `/logworks/<id>` | Admin | Delete logwork entry |

### Tickets (`/api/tickets`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/tickets` | Admin | List all tickets with pagination and filters |
| GET | `/tickets/my` | JWT | List tickets assigned to current user |
| GET | `/tickets/<id>` | JWT | Get ticket by UUID or ticket_id |
| GET | `/tickets/search` | JWT | Search tickets by ticket_id pattern |
| GET | `/tickets/project/<project_id>` | Admin | Get tickets for a project |
| POST | `/tickets` | JWT | Create single ticket |
| POST | `/tickets/bulk` | JWT | Bulk create tickets |
| POST | `/tickets/weeks` | JWT | Calculate week labels for a month |
| PUT | `/tickets/<id>` | JWT | Update ticket (admin or owner) |
| PUT | `/tickets/bulk` | JWT | Bulk update tickets |
| DELETE | `/tickets/<id>` | JWT | Delete ticket (admin or owner) |
| DELETE | `/tickets/bulk` | JWT | Bulk delete tickets |

### Ticket Types (`/api/ticket-types`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/ticket-types` | JWT | Get all ticket types |
| GET | `/ticket-types/<id>` | JWT | Get ticket type by UUID |
| POST | `/ticket-types` | Admin | Create ticket type |
| POST | `/ticket-types/bulk` | Admin | Bulk create ticket types |
| DELETE | `/ticket-types/<id>` | Admin | Delete ticket type |

### Ticket Statuses (`/api/ticket-statuses`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/ticket-statuses` | JWT | Get all ticket statuses |
| GET | `/ticket-statuses/<id>` | JWT | Get ticket status by UUID |
| POST | `/ticket-statuses` | Admin | Create ticket status |
| POST | `/ticket-statuses/bulk` | Admin | Bulk create ticket statuses |
| DELETE | `/ticket-statuses/<id>` | Admin | Delete ticket status |

### Formulas & KPI (`/api/formulas`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/formulas` | JWT | Get formulas and parameters for a month |
| PUT | `/formulas` | Admin | Update a formula string |
| PUT | `/formulas/params` | Admin | Update formula parameters for a month |
| POST | `/formulas/params` | Admin | Add new parameters or formulas |
| GET | `/formulas/kpi/closed-tickets` | Admin | KPI metrics for ticket closures |
| GET | `/formulas/list-employees-ee` | JWT | Active employees with total EE allocation |
| GET | `/formulas/calculate` | Admin | Calculate points for all employees |
| GET | `/formulas/calculate/<employee_id>` | JWT | Calculate points for one employee |

### Roles (`/api/roles`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/roles` | JWT | Get all roles |

### Export/Import (`/api/exports`)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/exports/tables` | Admin | List exportable DB tables and columns |
| POST | `/exports/excel/export` | Admin | Export database tables to Excel (.xlsx) |
| POST | `/exports/excel/import` | Admin | Import database from Excel (.xlsx) |

## Database Models

| Model | Table | Key Fields |
|-------|-------|------------|
| Employee | `employees` | id (UUID), employeeId, email, vn_full_name, en_full_name, authorize_role (MEMBER/ADMIN/MANAGER), status |
| Project | `projects` | id (UUID), project_id, name, pm_name, bank_id (FK), start_date, end_date |
| ProjectMember | `project_members` | id (UUID), user_id (FK), project_id (FK), role_id (FK), allocation_percent |
| Bank | `banks` | id (UUID), name |
| Ticket | `tickets` | id (UUID), ticket_id, project_id (FK), employee_id (FK), role_ids (UUID[]), ticket_type_id (FK), ticket_status_id (FK), week, month |
| TicketType | `ticket_types` | id (UUID), type_id, name |
| TicketStatus | `ticket_statuses` | id (UUID), status_id, name |
| Logwork | `logworks` | id (UUID), user_id (FK), project_id (FK), loghours (numeric), month, year |
| Role | `roles` | id (UUID), role_id, name |
| SystemParameter | `system_parameters` | id (UUID), param_key, param_value, description |

## Technology Stack

- **Framework**: Flask 3.1.2
- **Database**: PostgreSQL (with psycopg2-binary)
- **ORM**: SQLAlchemy 2.0.46
- **Authentication**: Flask-JWT-Extended 4.7.1 (JWT tokens)
- **Migrations**: Alembic 1.18.3 / Flask-Migrate 4.1.0
- **CORS**: Flask-CORS 6.0.2
- **Excel I/O**: openpyxl 3.1.5
- **HTTP Client**: requests 2.32.5
- **Python Version**: 3.12

## Setup Instructions

### Prerequisites
- Python 3.12+
- PostgreSQL 12+
- Docker & Docker Compose (optional)

### Local Installation

1. **Clone the repository**
   ```bash
   cd ~/projects
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source ./venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/employee_db

   # JWT Configuration
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here

   # Flask Configuration
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

5. **Create PostgreSQL database**
   ```bash
   createdb employee_db
   ```

6. **Run database migrations**
   ```bash
   flask db upgrade
   ```

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker compose up --build
   ```

   The compose setup:
   - Builds from the Dockerfile (Python 3.12-slim)
   - Maps port `8080:8080`
   - Loads environment from `.env`
   - Bind-mounts the project directory into the container
   - Logs output to `logs/app.log`

   > Note: No database service is defined in compose. The app expects external PostgreSQL connectivity via `SQLALCHEMY_DATABASE_URI`.

## Database Migration

### Run All Pending Migrations
```bash
flask db upgrade
```

### Create a New Migration
```bash
flask db migrate -m "describe your change"
flask db upgrade
```

### Initialize Migrations (first time only)
```bash
flask db init
```

## Running the Application

### Development Mode
```bash
python run.py
```

The application will start on `http://localhost:8080` with debug mode and auto-reload enabled.

## Configuration

**Location**: `app/config.py`

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | from `.env` |
| `JWT_SECRET_KEY` | JWT token signing key | from `.env` |
| `SQLALCHEMY_DATABASE_URI` | PostgreSQL connection string | from `.env` |
| `JWT_TOKEN_LOCATION` | Where to look for tokens | `["headers"]` |
| `JWT_HEADER_NAME` | Header name for JWT | `Authorization` |
| `JWT_HEADER_TYPE` | Token prefix | `Bearer` |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access token TTL | 1 hour |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh token TTL | 30 days |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | SQLAlchemy event tracking | `False` |

## Key Utilities

### Math Engine (`app/utils/math_engine.py`)
A custom formula parser and evaluator supporting:
- Arithmetic operations with proper precedence
- Variables and dynamic resolution
- Functions: `SUM`, `AVG`, `MIN`, `MAX`, `ABS`, `CUMSUM`, `SUM_IF`, `IF`
- Loop functions: `SIGMA`, `PRODUCT`
- Comparison operators in expressions

Used by the Formula service to calculate KPI points for employees based on configurable formulas stored in `system_parameters`.

### Number Parser (`app/utils/number_parser.py`)
Handles numeric string normalization for comma/dot decimal separators.

### Query Helpers (`app/utils/query_helpers.py`)
Parses comma-separated or list-style query parameters into typed lists.

## Development Notes

### Authentication & Authorization
- Token location: HTTP `Authorization` header
- Token format: `Bearer {token}`
- Access token expires in 1 hour
- Refresh token expires in 30 days
- Roles: `MEMBER`, `ADMIN`, `MANAGER`
- Admin endpoints are protected via `@admin_required` decorator

### Database
- PostgreSQL with SQLAlchemy ORM
- UUID primary keys (PostgreSQL native UUID type)
- Unique indexes on `employeeId`, `email`, `project_id`, `role_id`, `type_id`, `status_id`, `param_key`

### CORS
- Scope: `/api/*`
- Origins: `*`
- Allowed headers: `Content-Type`, `Authorization`, `ngrok-skip-browser-warning`
- Methods: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS`

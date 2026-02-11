# Employee Management API

A Flask-based REST API application for managing employee records with JWT authentication, built with SQLAlchemy ORM and PostgreSQL database.

## Project Overview

This project implements a modern web application architecture with separation of concerns:
- **Routes**: HTTP endpoint handlers
- **Services**: Business logic layer
- **DAO**: Data access objects for database operations
- **Models**: SQLAlchemy database models
- **Configuration**: Environment-based configuration management

## Project Structure

```
.
├── app/                          # Main application package
│   ├── __init__.py              # Flask app initialization
│   ├── config.py                # Configuration management
│   ├── models/                  # SQLAlchemy models
│   │   └── employee.py          # Employee model definition
│   ├── routes/                  # API endpoint handlers
│   │   ├── __init__.py
│   │   └── auth.py              # Authentication endpoints
│   ├── services/                # Business logic layer
│   │   └── auth.py              # Authentication service
│   ├── dao/                     # Data access objects
│   │   └── employee_dao.py      # Employee database operations
│   └── utils/                   # Helper functions
│       ├── auth_helpers.py      # Password verification utilities
│       └── decorators.py        # Custom decorators
├── migrations/                  # Alembic database migrations
│   ├── versions/                # Migration scripts
│   ├── env.py                   # Migration environment configuration
│   └── alembic.ini              # Alembic configuration
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker container configuration
├── docker-compose.yml           # Docker Compose setup
└── README.md                    # This file
```

## Architecture

### DAO (Data Access Object) Layer
**Location**: `app/dao/employee_dao.py`

The DAO layer handles all database operations and provides a clean interface for data access:

```python
class EmployeeDAO:
    @staticmethod
    def get_by_employee_id(employee_id: str)
    
    @staticmethod
    def get_by_employee_email(email: str)
    
    @staticmethod
    def update_password(employee: Employee, new_password: str)
```

**Responsibilities**:
- Query employee records from the database
- Create, update, delete operations
- Password management

### SERVICE Layer
**Location**: `app/services/auth.py`

The Service layer contains business logic and orchestrates DAO operations:

```python
class AuthService:
    @staticmethod
    def login(email: str, password: str)
    
    @staticmethod
    def get_current_employee(employee_id: str)
    
    @staticmethod
    def reset_password(employee_id: str, old_password: str, new_password: str)
```

**Responsibilities**:
- Authentication and authorization logic
- Password verification
- User session management
- Token generation and validation

### ROUTES Layer
**Location**: `app/routes/auth.py`

The Routes layer defines HTTP endpoints and handles request/response:

```
POST   /login              # User login with email and password
GET    /me                 # Get current user information (requires JWT)
POST   /reset-password     # Reset user password (requires JWT)
```

**Responsibilities**:
- HTTP request handling
- Request validation
- Response formatting
- JWT token requirement enforcement

## Technology Stack

- **Framework**: Flask 3.1.2
- **Database**: PostgreSQL (with psycopg2)
- **ORM**: SQLAlchemy 2.0.46
- **Authentication**: Flask-JWT-Extended (JWT tokens)
- **Migrations**: Alembic 1.18.3
- **Utilities**: Flask-CORS, Flask-SQLAlchemy, Flask-Migrate
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

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker compose up --build
   ```

## Database Migration

### Migration Scripts

#### Run All Pending Migrations (Upgrade)
    Run this script first to migrate all database
```bash
flask db upgrade
```

### Migration Examples

**Initialize Database Schema**

```bash
flask db init
flask db migrate -m "migrate db message"
flask db upgrade
```

## Running the Application

### Development Mode
```bash
python run.py
```

The application will start on `http://localhost:5000`


## Configuration

**Location**: `app/config.py`

Configuration is managed through environment variables:

```python
SECRET_KEY              # Flask secret key for session management
JWT_SECRET_KEY         # Secret key for JWT token signing
SQLALCHEMY_DATABASE_URI # PostgreSQL connection string
JWT_ACCESS_TOKEN_EXPIRES # Access token expiration (default: 1 hour)
JWT_REFRESH_TOKEN_EXPIRES # Refresh token expiration (default: 30 days)
```

## Development Notes

### JWT Tokens
- Token location: HTTP Authorization header
- Token format: `Bearer {token}`
- Access token expires in 1 hour
- Refresh token expires in 30 days

### Database
- PostgreSQL with SQLAlchemy ORM
- UUID primary keys (PostgreSQL native UUID type)
- Unique indexes on `employeeId` and `email`

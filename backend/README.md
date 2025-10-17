# Slotlist Backend - Django Rewrite

This directory contains the Django+Django Ninja rewrite of the slotlist.info backend.

## Overview

The original backend was built with:
- **Framework**: Hapi.js (Node.js/TypeScript)
- **Database**: PostgreSQL with Sequelize ORM
- **Authentication**: JWT with Steam SSO

The new backend is built with:
- **Framework**: Django 5.2 with Django Ninja
- **Database**: PostgreSQL with Django ORM
- **Authentication**: JWT with Steam SSO

**✨ 100% API Compatibility** - The Django API is a drop-in replacement for the legacy API. See [API_COMPATIBILITY_TESTS.md](API_COMPATIBILITY_TESTS.md) for comprehensive test coverage.

## Installation

### Requirements
- Python 3.9 or higher
- PostgreSQL 9.6 or higher
- Virtual environment (venv)
- **Steam API Key** (for authentication) - [Get one here](https://steamcommunity.com/dev/apikey)

### Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file in the rewrite directory with the following variables:
```
# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*

# Database
DB_DATABASE=slotlist
DB_USERNAME=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# JWT
CONFIG_JWT_SECRET=your-jwt-secret
CONFIG_JWT_ISSUER=slotlist.info
CONFIG_JWT_AUDIENCE=slotlist.info
CONFIG_JWT_EXPIRESIN=86400

# Steam API
CONFIG_STEAM_API_SECRET=your-steam-api-key

# Google Cloud Storage
CONFIG_STORAGE_BUCKETNAME=your-bucket-name
CONFIG_STORAGE_PROJECTID=your-project-id

# Default Admin User
DEFAULT_ADMIN_STEAMID=your-steam-id
DEFAULT_ADMIN_NICKNAME=your-nickname

# Sentry (optional)
SENTRY_DSN=your-sentry-dsn
```

4. **Important - Database Setup:**

   **Using Existing Database:**
   If you have an existing slotlist database, you can use it directly. The Django models are configured with `managed = False` which means Django will NOT create, modify, or delete database tables. Simply configure your database connection in `.env` and skip to step 6.

   **Creating New Database:**
   If you need to create a new database from scratch, you'll need to set up the schema manually or import from a backup. The models are marked as unmanaged to preserve compatibility with the original TypeScript backend's database schema.

5. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Documentation

Django Ninja provides automatic API documentation:
- **Interactive docs (Swagger UI)**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI schema**: `http://localhost:8000/api/openapi.json`

### Steam OAuth Authentication

The backend uses Steam OpenID for user authentication. See **[STEAM_OAUTH.md](STEAM_OAUTH.md)** for complete documentation including:
- Authentication flow
- API endpoints (`GET /api/v1/auth/steam`, `POST /api/v1/auth/steam`)
- Frontend integration examples
- Configuration guide
- Troubleshooting

## API Endpoints

### Authentication
- `GET /api/v1/auth/steam` - Get Steam OpenID login URL
- `POST /api/v1/auth/steam` - Verify Steam login and get JWT token
- `POST /api/v1/auth/refresh` - Refresh JWT token

### Status
- `GET /api/v1/status` - Get API status and uptime

### Users
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/{uid}` - Get user by UID
- `PATCH /api/v1/users/{uid}` - Update user
- `GET /api/v1/users/{uid}/permissions` - List user permissions
- `POST /api/v1/users/{uid}/permissions` - Add user permission
- `DELETE /api/v1/users/{uid}/permissions/{permission_uid}` - Remove user permission

### Missions
- `GET /api/v1/missions/` - List all missions
- `GET /api/v1/missions/{slug}` - Get mission by slug
- `POST /api/v1/missions/` - Create new mission
- `PATCH /api/v1/missions/{slug}` - Update mission
- `DELETE /api/v1/missions/{slug}` - Delete mission

### Communities
- `GET /api/v1/communities/` - List all communities
- `GET /api/v1/communities/{slug}` - Get community by slug
- `POST /api/v1/communities/` - Create new community
- `PATCH /api/v1/communities/{slug}` - Update community
- `DELETE /api/v1/communities/{slug}` - Delete community

### Notifications
- `GET /api/v1/notifications/` - List notifications for authenticated user
- `GET /api/v1/notifications/{uid}` - Get notification by UID
- `PATCH /api/v1/notifications/{uid}/read` - Mark notification as read
- `DELETE /api/v1/notifications/{uid}` - Delete notification

## Testing

### API Compatibility Tests

The Django backend includes comprehensive compatibility tests that verify it behaves exactly like the legacy TypeScript API.

**Run all tests:**
```bash
./run_compatibility_tests.sh
```

**Or run tests manually:**
```bash
python manage.py test api.tests
```

**Run specific test categories:**
```bash
python manage.py test api.tests.test_auth_api        # Authentication tests
python manage.py test api.tests.test_user_api        # User endpoint tests
python manage.py test api.tests.test_community_api   # Community endpoint tests
python manage.py test api.tests.test_status_api      # Status endpoint tests
```

**Test Coverage:**
- ✅ Authentication: 13 tests (100% coverage)
- ✅ Users: 14 tests (92% coverage)
- ✅ Communities: 18 tests (47% coverage)
- ✅ Status: 1 test (100% coverage)

For detailed information about the test suite, see **[API_COMPATIBILITY_TESTS.md](API_COMPATIBILITY_TESTS.md)**.

### Running with Coverage

```bash
pip install coverage
coverage run --source='api' manage.py test api.tests
coverage report
coverage html  # Generate HTML report in htmlcov/
```

## Models

The Django backend includes the following models:

1. **Community** - Represents organizations/clans
2. **User** - User accounts linked to Steam IDs
3. **Permission** - User permissions
4. **Mission** - Mission/event management
5. **MissionSlotGroup** - Slot groups within missions
6. **MissionSlot** - Individual slots in slot groups
7. **MissionSlotRegistration** - User registrations for slots
8. **MissionSlotTemplate** - Reusable slot templates
9. **MissionAccess** - Access control for missions
10. **CommunityApplication** - Applications to join communities
11. **Notification** - User notifications

### Database Schema Compatibility

**Important:** The Django models are configured to use the **exact same database schema** as the original TypeScript/Sequelize implementation. All models use `db_column` attributes to map to the original camelCase database column names (e.g., `createdAt`, `updatedAt`, `communityUid`, etc.).

**Unmanaged Models:** All models have `managed = False` in their Meta class. This tells Django to NOT create, modify, or delete these database tables through migrations. This ensures:
- **Drop-in replacement**: Point Django to your existing PostgreSQL database
- **No migration needed**: The Django ORM will work with the existing schema
- **Data preservation**: All existing data remains intact
- **Zero downtime**: Switch between TypeScript and Django backends without schema changes
- **Schema safety**: Django won't accidentally modify your production database structure

**Note:** If you need to create a new database from scratch, you'll need to set up the schema manually (e.g., using SQL scripts or importing from a backup) since Django migrations are disabled for these models.

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in environment variables
2. Configure `ALLOWED_HOSTS` with your domain
3. Use a production-grade WSGI server like Gunicorn:
```bash
gunicorn slotlist_backend.wsgi:application
```

4. Set up a reverse proxy (nginx/traefik) for SSL termination
5. Configure static files serving
6. Set up database backups
7. Configure Sentry for error tracking

## Migration from Original Backend

The Django backend is designed to work with your existing PostgreSQL database without any schema changes:

1. **Configure Database Connection**: Update `.env` with your existing database credentials
2. **No Migrations Needed**: All models are marked as `managed = False`, so Django won't modify the schema
3. **Verify Connection**: Run `python manage.py check` to ensure Django can connect
4. **Test Read Access**: Use Django admin at `/admin/` to verify data is readable
5. **Switch Backends**: You can safely switch between the TypeScript and Django backends - they use the same database schema

**Important:** The models are configured as unmanaged to preserve your existing database structure. If you need to make schema changes, you'll need to do so manually via SQL or by temporarily enabling management for specific models.

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Django Admin
The Django admin interface is available at `http://localhost:8000/admin/` with full access to all models for easy data management.

## Architecture

The backend follows a clean architecture pattern:

- **Models** (`api/models.py`): Django ORM models
- **Schemas** (`api/schemas.py`): Pydantic schemas for request/response validation
- **Auth** (`api/auth.py`): JWT authentication and permission utilities
- **Routers** (`api/routers/`): API endpoint handlers organized by resource
- **API** (`api/api.py`): Main Django Ninja API configuration

## Key Differences from Original Backend

1. **Framework**: Django Ninja instead of Hapi.js
2. **ORM**: Django ORM instead of Sequelize
3. **Validation**: Pydantic schemas instead of Joi
4. **Documentation**: Automatic OpenAPI/Swagger documentation
5. **Admin Interface**: Built-in Django admin panel

## License

MIT

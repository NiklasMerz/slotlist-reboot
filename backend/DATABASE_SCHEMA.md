# Database Schema Compatibility

This Django backend is designed to be **100% compatible** with the existing TypeScript/Sequelize database schema.

## Schema Mapping

All Django models use explicit `db_column` attributes to ensure they map to the exact camelCase column names used in the original database:

### Column Name Mapping

| Django Model Field | Database Column Name |
|-------------------|---------------------|
| `created_at` | `createdAt` |
| `updated_at` | `updatedAt` |
| `steam_id` | `steamId` |
| `community` (FK) | `communityUid` |
| `creator` (FK) | `creatorUid` |
| `user` (FK) | `userUid` |
| `mission` (FK) | `missionUid` |
| `slot_group` (FK) | `slotGroupUid` |
| `assignee` (FK) | `assigneeUid` |
| `briefing_time` | `briefingTime` |
| `slotting_time` | `slottingTime` |
| `start_time` | `startTime` |
| `end_time` | `endTime` |
| `logo_url` | `logoUrl` |
| `banner_image_url` | `bannerImageUrl` |
| `game_servers` | `gameServers` |
| `voice_comms` | `voiceComms` |
| `required_dlcs` | `requiredDLCs` |
| `order_number` | `orderNumber` |
| `detailed_description` | `detailedDescription` |
| `collapsed_description` | `collapsedDescription` |
| `short_description` | `shortDescription` |
| `tech_support` | `techSupport` |
| `details_map` | `detailsMap` |
| `details_game_mode` | `detailsGameMode` |
| `mission_token` | `missionToken` |
| `restricted_community` (FK) | `restrictedCommunityUid` |
| `external_assignee` | `externalAssignee` |
| `auto_assignable` | `autoAssignable` |
| `slot` (FK) | `slotUid` |
| `slot_groups` | `slotGroups` |
| `application_text` | `applicationText` |
| `notification_type` | `notificationType` |
| `additional_data` | `additionalData` |

## Table Names

All Django models use the exact same table names as the original:

- `communities`
- `users`
- `permissions`
- `missions`
- `missionSlotGroups`
- `missionSlots`
- `missionSlotRegistrations`
- `missionSlotTemplates`
- `missionAccesses`
- `communityApplications`
- `notifications`

## Field Types

Field types are mapped exactly:

- **UUID fields**: Use `models.UUIDField`
- **String fields**: Use `models.CharField` or `models.TextField`
- **JSON fields**: Use `models.JSONField` (PostgreSQL JSONB)
- **DateTime fields**: Use `models.DateTimeField`
- **Boolean fields**: Use `models.BooleanField`
- **Integer fields**: Use `models.IntegerField`

## Foreign Keys

All foreign key relationships are preserved with the correct:
- **on_delete behavior**: CASCADE, SET NULL, etc.
- **related_name**: For reverse lookups
- **db_column**: Points to the original camelCase UID columns

## Usage with Existing Database

### 1. Configure Database Connection

Update your `.env` file with existing database credentials:

```env
DB_DATABASE=slotlist
DB_USERNAME=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

### 2. No Migrations Needed

**Do NOT run `python manage.py migrate`** against an existing database. The Django models are already configured to match the existing schema.

If you want Django to track migrations, you can run:
```bash
python manage.py migrate --fake-initial
```

This tells Django the tables already exist and just records the migration without creating tables.

### 3. Test Connectivity

```bash
python manage.py shell
```

Then test:
```python
from api.models import User, Community, Mission
print(User.objects.count())
print(Community.objects.count())
print(Mission.objects.count())
```

## Creating New Database

If you're creating a fresh database:

1. Create the database:
```sql
CREATE DATABASE slotlist;
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create admin user (if needed):
```bash
python manage.py createsuperuser
```

## Differences from Original Implementation

### Removed Fields
- `deletedAt` columns have been removed (paranoid/soft delete not used in Django implementation)

### Field Behavior
- Django auto-manages `createdAt` and `updatedAt` with `auto_now_add` and `auto_now`
- Default values for JSON fields use Python `list` instead of empty arrays
- UUID fields use Python's `uuid.uuid4` for default values

## Verification

To verify the schema matches, you can compare:

1. **Check table structure**:
```sql
\d+ missions
\d+ users
\d+ communities
```

2. **Compare with TypeScript migrations** in `src/shared/migrations/`

3. **Test CRUD operations** through Django ORM to ensure compatibility

## Migration Path

For switching from TypeScript to Django backend:

1. **Keep both backends running** (optional for testing)
2. **Point Django to existing database**
3. **Test all API endpoints** with existing data
4. **Switch traffic** to Django backend
5. **Decommission** TypeScript backend when confident

No downtime required - both backends can read/write to the same database simultaneously.

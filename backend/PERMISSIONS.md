# Permission System Documentation

## Overview

The Django backend implements the same permission system as the original TypeScript backend, with full support for hierarchical permissions, wildcards, and admin privileges.

## Permission Structure

Permissions use a **dotted notation** with hierarchical structure:

```
category.resource.action
```

### Examples

```
admin.user              # User administration
admin.community         # Community administration
admin.permission        # Permission administration
admin.superadmin        # Super admin (grants all permissions)
community.test.leader   # Leader of the "test" community
mission.op-1.editor     # Editor of the "op-1" mission
```

## Wildcard Support

The permission system supports **wildcards** for granting broader access:

### Global Wildcard

```
*
```
Grants access to **everything**. Should be used sparingly.

### Category Wildcard

```
admin.*
```
Grants access to all admin permissions (user, community, permission, etc.)

### Partial Wildcards

```
community.test.*
```
Grants all permissions for the "test" community (leader, recruitment, etc.)

## Permission Hierarchy

The system uses a **tree-based** permission structure that's parsed from dotted notation:

```python
permissions = ['admin.user', 'community.test.leader', 'admin.*']
```

Gets parsed into:

```python
{
    'admin': {
        'user': {},
        '*': {}      # Wildcard grants all admin permissions
    },
    'community': {
        'test': {
            'leader': {}
        }
    }
}
```

## Special Permissions

### Super Admin

```
admin.superadmin
```

The `admin.superadmin` permission **implicitly grants all other permissions** in the system, similar to the global wildcard `*`.

## Permission Validation

### Community Permissions

Valid community permissions follow these formats:

- `community.{slug}.leader` - Community leadership role
- `community.{slug}.recruitment` - Community recruitment management

Example:
```python
from api.models import Permission

# Validate community permission
is_valid = Permission.is_valid_community_permission('test-community', 'community.test-community.leader')
# Returns: True
```

### Mission Permissions

Valid mission permissions follow these formats:

- `mission.{slug}.editor` - Mission editor role
- `mission.{slug}.slotlist.community` - Community-level slotlist access

Example:
```python
from api.models import Permission

# Validate mission permission
is_valid = Permission.is_valid_mission_permission('operation-1', 'mission.operation-1.editor')
# Returns: True
```

## Using Permissions in API Endpoints

### Importing

```python
from api.auth import has_permission
```

### Checking Single Permission

```python
@router.post('/communities/', response=CommunitySchema)
def create_community(request, payload: CommunityCreateSchema):
    permissions = request.auth.get('permissions', [])
    
    if not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    # ... create community
```

### Checking Multiple Permissions (OR logic)

```python
@router.patch('/missions/{slug}', response=MissionSchema)
def update_mission(request, slug: str, payload: MissionUpdateSchema):
    permissions = request.auth.get('permissions', [])
    
    # User needs EITHER admin.mission OR mission.{slug}.editor
    if not has_permission(permissions, ['admin.mission', f'mission.{slug}.editor']):
        return 403, {'detail': 'Forbidden'}
    
    # ... update mission
```

### Checking Community-Specific Permissions

```python
@router.post('/communities/{slug}/permissions', response=PermissionSchema)
def create_community_permission(request, slug: str, payload: PermissionCreateSchema):
    permissions = request.auth.get('permissions', [])
    
    # User needs admin.community OR community.{slug}.leader
    required_perms = ['admin.community', f'community.{slug}.leader']
    if not has_permission(permissions, required_perms):
        return 403, {'detail': 'Forbidden'}
    
    # Validate the permission being granted
    if not Permission.is_valid_community_permission(slug, payload.permission):
        return 400, {'detail': 'Invalid community permission'}
    
    # ... create permission
```

## Permission Examples

### Admin Permissions

```python
'*'                    # Global admin (everything)
'admin.superadmin'     # Super admin (everything)
'admin.*'              # All admin functions
'admin.user'           # User management
'admin.community'      # Community management
'admin.mission'        # Mission management
'admin.permission'     # Permission management
```

### Community Permissions

```python
'community.*'                      # All communities (broad)
'community.test.*'                 # All permissions for test community
'community.test.leader'            # Leader of test community
'community.test.recruitment'       # Recruitment manager for test community
```

### Mission Permissions

```python
'mission.*'                        # All missions (broad)
'mission.operation-1.*'            # All permissions for operation-1
'mission.operation-1.editor'       # Editor for operation-1
'mission.operation-1.slotlist.community'  # Community slotlist access
```

## API Functions

### `has_permission(permissions: list, target_permissions: str | list) -> bool`

Check if a user has required permission(s).

**Parameters:**
- `permissions`: List of permission strings the user has
- `target_permissions`: Permission(s) to check for (string or list)

**Returns:**
- `bool`: Whether user has at least one of the target permissions

**Examples:**

```python
# Single permission check
has_permission(['admin.user', 'admin.community'], 'admin.user')
# Returns: True

# Multiple permission check (OR logic)
has_permission(['community.test.leader'], ['admin.community', 'community.test.leader'])
# Returns: True (has one of them)

# Wildcard check
has_permission(['admin.*'], 'admin.user')
# Returns: True (wildcard matches)

# Super admin check
has_permission(['admin.superadmin'], 'anything.at.all')
# Returns: True (superadmin has everything)
```

### `find_permission(permission_tree: dict, target_permission: str | list) -> bool`

Recursively search for permission in parsed permission tree.

**Parameters:**
- `permission_tree`: Parsed permission tree (from `parse_permissions`)
- `target_permission`: Permission to find (string or list of parts)

**Returns:**
- `bool`: Whether permission was found

### `parse_permissions(permissions: list) -> dict`

Parse flat list of permission strings into hierarchical tree.

**Parameters:**
- `permissions`: List of permission strings

**Returns:**
- `dict`: Hierarchical permission tree

**Example:**

```python
parse_permissions(['admin.user', 'admin.community', 'community.test.leader'])
# Returns:
# {
#     'admin': {
#         'user': {},
#         'community': {}
#     },
#     'community': {
#         'test': {
#             'leader': {}
#         }
#     }
# }
```

## Database Schema

Permissions are stored in the `permissions` table:

```sql
CREATE TABLE permissions (
    uid UUID PRIMARY KEY,
    "userUid" UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
    permission VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
    "updatedAt" TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE("userUid", permission)
);
```

## JWT Token Structure

Permissions are included in JWT tokens:

```json
{
  "user": {
    "uid": "user-uuid",
    "nickname": "TestUser",
    "steam_id": "76561198000000000",
    "community": { ... },
    "active": true
  },
  "permissions": [
    "admin.user",
    "community.test.leader"
  ],
  "iat": 1234567890,
  "exp": 1234654290,
  "iss": "slotlist.info",
  "aud": "slotlist.info",
  "sub": "user-uuid"
}
```

## Testing Permissions

### Manual Testing with cURL

```bash
# Get JWT token first (via Steam auth)
TOKEN="your-jwt-token"

# Test with permission
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/communities/

# Should succeed if user has required permissions
```

### Testing in Python

```python
from api.auth import has_permission, parse_permissions

# Test basic permission
permissions = ['admin.user', 'community.test.leader']
assert has_permission(permissions, 'admin.user') == True
assert has_permission(permissions, 'admin.community') == False

# Test wildcard
permissions = ['admin.*']
assert has_permission(permissions, 'admin.user') == True
assert has_permission(permissions, 'admin.community') == True
assert has_permission(permissions, 'community.test.leader') == False

# Test superadmin
permissions = ['admin.superadmin']
assert has_permission(permissions, 'anything.at.all') == True

# Test global wildcard
permissions = ['*']
assert has_permission(permissions, 'anything') == True
```

## Best Practices

1. **Use specific permissions** when possible (e.g., `admin.user` instead of `admin.*`)

2. **Validate permissions** before granting them:
   ```python
   if not Permission.is_valid_community_permission(slug, permission):
       return 400, {'detail': 'Invalid permission'}
   ```

3. **Check permissions early** in endpoint handlers:
   ```python
   if not has_permission(permissions, required_permission):
       return 403, {'detail': 'Forbidden'}
   ```

4. **Use OR logic** for resource-specific permissions:
   ```python
   # Allow either admin OR resource owner
   required = ['admin.mission', f'mission.{slug}.editor']
   if not has_permission(permissions, required):
       return 403, {'detail': 'Forbidden'}
   ```

5. **Log permission checks** in production for auditing

6. **Never hardcode** user UIDs or permissions in code

## Migration from Legacy

The Django permission system is **100% compatible** with the TypeScript implementation:

- ✅ Same dotted notation
- ✅ Same wildcard support
- ✅ Same `admin.superadmin` behavior
- ✅ Same permission validation rules
- ✅ Same database schema
- ✅ Same JWT structure

No changes needed to existing permissions in the database when migrating.

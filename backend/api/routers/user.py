from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from api.models import User, Permission
from api.schemas import UserSchema, UserDetailSchema, UserUpdateSchema, PermissionSchema
from api.auth import has_permission

router = Router()


@router.get('/', response=List[UserSchema])
def list_users(request, limit: int = 25, offset: int = 0):
    """List all users with pagination"""
    users = User.objects.select_related('community').all()[offset:offset + limit]
    return [
        {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': None,  # Don't expose by default
            'community': {
                'uid': user.community.uid,
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug,
                'website': user.community.website,
                'image_url': user.community.image_url,
                'game_servers': user.community.game_servers,
                'voice_comms': user.community.voice_comms,
                'repositories': user.community.repositories
            } if user.community else None,
            'active': None
        }
        for user in users
    ]


@router.get('/{user_uid}', response=UserDetailSchema)
def get_user(request, user_uid: UUID):
    """Get a single user by UID"""
    user = get_object_or_404(User.objects.select_related('community').prefetch_related('missions'), uid=user_uid)
    
    # Check if requesting user has admin permissions
    include_admin_details = False
    if request.auth:
        permissions = request.auth.get('permissions', [])
        include_admin_details = has_permission(permissions, 'admin.user')
    
    return {
        'uid': user.uid,
        'nickname': user.nickname,
        'steam_id': user.steam_id if include_admin_details else None,
        'community': {
            'uid': user.community.uid,
            'name': user.community.name,
            'tag': user.community.tag,
            'slug': user.community.slug,
            'website': user.community.website,
            'image_url': user.community.image_url,
            'game_servers': user.community.game_servers,
            'voice_comms': user.community.voice_comms,
            'repositories': user.community.repositories
        } if user.community else None,
        'active': user.active if include_admin_details else None,
        'missions': []  # Would need to populate this
    }


@router.patch('/{user_uid}', response=UserSchema)
def update_user(request, user_uid: UUID, payload: UserUpdateSchema):
    """Update a user"""
    user = get_object_or_404(User, uid=user_uid)
    
    # Check if user can update (must be self or admin)
    auth_user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    if str(user.uid) != auth_user_uid and not has_permission(permissions, 'admin.user'):
        return 403, {'detail': 'Forbidden'}
    
    # Update user fields
    if payload.nickname is not None:
        user.nickname = payload.nickname
    
    user.save()
    
    return {
        'uid': user.uid,
        'nickname': user.nickname,
        'steam_id': None,
        'community': {
            'uid': user.community.uid,
            'name': user.community.name,
            'tag': user.community.tag,
            'slug': user.community.slug,
            'website': user.community.website,
            'image_url': user.community.image_url,
            'game_servers': user.community.game_servers,
            'voice_comms': user.community.voice_comms,
            'repositories': user.community.repositories
        } if user.community else None,
        'active': None
    }


@router.get('/{user_uid}/permissions', response=List[PermissionSchema])
def list_user_permissions(request, user_uid: UUID):
    """List permissions for a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    user_permissions = Permission.objects.filter(user__uid=user_uid)
    return [
        {'uid': perm.uid, 'permission': perm.permission}
        for perm in user_permissions
    ]


@router.post('/{user_uid}/permissions', response=PermissionSchema)
def create_user_permission(request, user_uid: UUID, permission: str):
    """Add a permission to a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    user = get_object_or_404(User, uid=user_uid)
    perm, created = Permission.objects.get_or_create(user=user, permission=permission)
    
    return {'uid': perm.uid, 'permission': perm.permission}


@router.delete('/{user_uid}/permissions/{permission_uid}')
def delete_user_permission(request, user_uid: UUID, permission_uid: UUID):
    """Remove a permission from a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    permission = get_object_or_404(Permission, uid=permission_uid, user__uid=user_uid)
    permission.delete()
    
    return {'success': True}

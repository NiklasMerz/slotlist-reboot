from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from typing import Optional, Any, List as ListType
from uuid import UUID
from api.models import MissionSlotTemplate, User, Community
from api.auth import has_permission

router = Router()


class MissionSlotTemplateCreateSchema(Schema):
    title: str
    slotGroups: ListType[Any]
    communityUid: Optional[UUID] = None


class MissionSlotTemplateUpdateSchema(Schema):
    title: Optional[str] = None
    slotGroups: Optional[ListType[Any]] = None
    communityUid: Optional[UUID] = None


@router.get('/', auth=None)
def list_mission_slot_templates(request, limit: int = 25, offset: int = 0):
    """List all mission slot templates with pagination"""
    total = MissionSlotTemplate.objects.count()
    templates = MissionSlotTemplate.objects.select_related('creator', 'community').all()[offset:offset + limit]
    
    return {
        'slotTemplates': [
            {
                'uid': str(template.uid),
                'title': template.title,
                'slotGroups': template.slot_groups,
                'creator': {
                    'uid': str(template.creator.uid),
                    'nickname': template.creator.nickname,
                },
                'community': {
                    'uid': str(template.community.uid),
                    'name': template.community.name,
                    'tag': template.community.tag,
                    'slug': template.community.slug,
                } if template.community else None,
                'createdAt': template.created_at.isoformat() if template.created_at else None,
                'updatedAt': template.updated_at.isoformat() if template.updated_at else None,
            }
            for template in templates
        ],
        'total': total
    }


@router.get('/{uid}', auth=None)
def get_mission_slot_template(request, uid: UUID):
    """Get a single mission slot template by UID"""
    template = get_object_or_404(MissionSlotTemplate.objects.select_related('creator', 'community'), uid=uid)
    
    # Ensure each slot group has a slots array
    slot_groups = template.slot_groups or []
    # Make a copy to avoid modifying the original
    slot_groups_copy = []
    for group in slot_groups:
        if isinstance(group, dict):
            # It's already a dict, ensure it has slots
            group_copy = dict(group)
            if 'slots' not in group_copy:
                group_copy['slots'] = []
            slot_groups_copy.append(group_copy)
        else:
            # Skip non-dict items
            continue
    
    return {
        'slotTemplate': {
            'uid': str(template.uid),
            'title': template.title,
            'slotGroups': slot_groups_copy,
            'creator': {
                'uid': str(template.creator.uid),
                'nickname': template.creator.nickname,
            },
            'community': {
                'uid': str(template.community.uid),
                'name': template.community.name,
                'tag': template.community.tag,
                'slug': template.community.slug,
            } if template.community else None,
            'createdAt': template.created_at.isoformat() if template.created_at else None,
            'updatedAt': template.updated_at.isoformat() if template.updated_at else None,
        }
    }


@router.post('/')
def create_mission_slot_template(request, payload: MissionSlotTemplateCreateSchema):
    """Create a new mission slot template"""
    if not request.auth:
        return 401, {'detail': 'Authentication required'}
    
    user_uid = request.auth.get('user', {}).get('uid')
    if not user_uid:
        return 401, {'detail': 'Invalid authentication'}
    
    user = get_object_or_404(User, uid=user_uid)
    
    community = None
    if payload.communityUid:
        community = get_object_or_404(Community, uid=payload.communityUid)
    
    template = MissionSlotTemplate.objects.create(
        title=payload.title,
        slot_groups=payload.slotGroups,
        creator=user,
        community=community
    )
    
    # Ensure slot groups have slots arrays
    slot_groups = template.slot_groups or []
    slot_groups_copy = []
    for group in slot_groups:
        if isinstance(group, dict):
            group_copy = dict(group)
            if 'slots' not in group_copy:
                group_copy['slots'] = []
            slot_groups_copy.append(group_copy)
    
    return {
        'slotTemplate': {
            'uid': str(template.uid),
            'title': template.title,
            'slotGroups': slot_groups_copy,
            'creator': {
                'uid': str(template.creator.uid),
                'nickname': template.creator.nickname,
            },
            'community': {
                'uid': str(template.community.uid),
                'name': template.community.name,
                'tag': template.community.tag,
                'slug': template.community.slug,
            } if template.community else None,
            'createdAt': template.created_at.isoformat() if template.created_at else None,
            'updatedAt': template.updated_at.isoformat() if template.updated_at else None,
        }
    }


@router.delete('/{uid}')
def delete_mission_slot_template(request, uid: UUID):
    """Delete a mission slot template"""
    template = get_object_or_404(MissionSlotTemplate, uid=uid)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(template.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.slotTemplate')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    template.delete()
    return {'success': True}


@router.patch('/{uid}', response={200: dict, 401: dict, 403: dict})
def update_mission_slot_template(request, uid: UUID, payload: MissionSlotTemplateUpdateSchema):
    """Update a mission slot template"""
    if not request.auth:
        return 401, {'detail': 'Authentication required'}
    
    template = get_object_or_404(MissionSlotTemplate, uid=uid)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(template.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.slotTemplate')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    # Update fields
    if payload.title is not None:
        template.title = payload.title
    if payload.slotGroups is not None:
        template.slot_groups = payload.slotGroups
    if payload.communityUid is not None:
        community = get_object_or_404(Community, uid=payload.communityUid)
        template.community = community
    
    template.save()
    
    # Ensure slot groups have slots arrays
    slot_groups = template.slot_groups or []
    slot_groups_copy = []
    for group in slot_groups:
        if isinstance(group, dict):
            group_copy = dict(group)
            if 'slots' not in group_copy:
                group_copy['slots'] = []
            slot_groups_copy.append(group_copy)
    
    return {
        'slotTemplate': {
            'uid': str(template.uid),
            'title': template.title,
            'slotGroups': slot_groups_copy,
            'creator': {
                'uid': str(template.creator.uid),
                'nickname': template.creator.nickname,
            },
            'community': {
                'uid': str(template.community.uid),
                'name': template.community.name,
                'tag': template.community.tag,
                'slug': template.community.slug,
            } if template.community else None,
            'createdAt': template.created_at.isoformat() if template.created_at else None,
            'updatedAt': template.updated_at.isoformat() if template.updated_at else None,
        }
    }

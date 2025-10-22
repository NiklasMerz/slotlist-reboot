from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from typing import Optional, Any, List as ListType
from uuid import UUID
from api.models import MissionSlotTemplate, User, Community
from api.auth import has_permission

router = Router()


class MissionSlotTemplateCreateSchema(Schema):
    title: str
    slot_groups: ListType[Any]
    community_uid: Optional[UUID] = None


@router.get('/', auth=None)
def list_mission_slot_templates(request, limit: int = 25, offset: int = 0):
    """List all mission slot templates with pagination"""
    templates = MissionSlotTemplate.objects.select_related('creator', 'community').all()[offset:offset + limit]
    
    result = []
    for template in templates:
        result.append({
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
        })
    
    return result


@router.get('/{uid}', auth=None)
def get_mission_slot_template(request, uid: UUID):
    """Get a single mission slot template by UID"""
    template = get_object_or_404(MissionSlotTemplate.objects.select_related('creator', 'community'), uid=uid)
    
    return {
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


@router.post('/')
def create_mission_slot_template(request, payload: MissionSlotTemplateCreateSchema):
    """Create a new mission slot template"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    community = None
    if payload.community_uid:
        community = get_object_or_404(Community, uid=payload.community_uid)
    
    template = MissionSlotTemplate.objects.create(
        title=payload.title,
        slot_groups=payload.slot_groups,
        creator=user,
        community=community
    )
    
    return {
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

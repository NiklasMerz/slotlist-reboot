from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from datetime import datetime
from django.utils.text import slugify
from api.models import Mission, Community, User, MissionSlotGroup, MissionSlot
from api.schemas import MissionSchema, MissionCreateSchema, MissionUpdateSchema
from api.auth import has_permission

router = Router()


@router.get('/', auth=None)
def list_missions(request, limit: int = 25, offset: int = 0, include_ended: bool = False, startDate: int = None, endDate: int = None):
    """List all missions with pagination"""
    query = Mission.objects.select_related('creator', 'community').all()
    
    # Date range filtering for calendar
    if startDate and endDate:
        from datetime import datetime as dt, timezone
        start_dt = dt.fromtimestamp(startDate / 1000, tz=timezone.utc)
        end_dt = dt.fromtimestamp(endDate / 1000, tz=timezone.utc)
        query = query.filter(start_time__gte=start_dt, start_time__lte=end_dt)
    elif not include_ended:
        query = query.filter(end_time__gte=datetime.utcnow()) | query.filter(end_time__isnull=True)
    
    missions = query[offset:offset + limit]
    
    result = []
    for mission in missions:
        result.append({
            'uid': str(mission.uid),
            'slug': mission.slug,
            'title': mission.title,
            'description': mission.description,
            'briefing_time': mission.briefing_time.isoformat() if mission.briefing_time else None,
            'slotting_time': mission.slotting_time.isoformat() if mission.slotting_time else None,
            'start_time': mission.start_time.isoformat() if mission.start_time else None,
            'end_time': mission.end_time.isoformat() if mission.end_time else None,
            'visibility': mission.visibility,
            'details_map': mission.details_map,
            'details_game_mode': mission.details_game_mode,
            'required_dlcs': mission.required_dlcs,
            'banner_image_url': mission.banner_image_url,
            'creator': {
                'uid': str(mission.creator.uid),
                'nickname': mission.creator.nickname,
                'steam_id': mission.creator.steam_id,
            },
            'community': {
                'uid': str(mission.community.uid),
                'name': mission.community.name,
                'tag': mission.community.tag,
                'slug': mission.community.slug,
                'website': mission.community.website,
                'logo_url': mission.community.logo_url,
            } if mission.community else None
        })
    
    return result


@router.get('/{slug}', response=MissionSchema, auth=None)
def get_mission(request, slug: str):
    """Get a single mission by slug"""
    mission = get_object_or_404(Mission.objects.select_related('creator', 'community'), slug=slug)
    
    return {
        'uid': mission.uid,
        'slug': mission.slug,
        'title': mission.title,
        'description': mission.description,
        'briefing_time': mission.briefing_time,
        'slot_list_time': mission.slotting_time,
        'start_time': mission.start_time,
        'end_time': mission.end_time,
        'visibility': mission.visibility,
        'tech_support': mission.tech_support,
        'details_map': mission.details_map,
        'details_game_mode': mission.details_game_mode,
        'details_required_dlcs': mission.required_dlcs,
        'game_server': mission.game_server,
        'voice_comms': mission.voice_comms,
        'repositories': mission.repositories,
        'rules_of_engagement': mission.rules,
        'image_url': mission.image_url,
        'creator': {
            'uid': mission.creator.uid,
            'nickname': mission.creator.nickname,
            'steam_id': None,
            'community': None,
            'active': None
        },
        'community': {
            'uid': mission.community.uid,
            'name': mission.community.name,
            'tag': mission.community.tag,
            'slug': mission.community.slug,
            'website': mission.community.website,
            'image_url': mission.community.image_url,
            'game_servers': mission.community.game_servers,
            'voice_comms': mission.community.voice_comms,
            'repositories': mission.community.repositories
        } if mission.community else None
    }


@router.post('/', response=MissionSchema)
def create_mission(request, payload: MissionCreateSchema):
    """Create a new mission"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    # Get community if specified
    community = None
    if payload.community_uid:
        community = get_object_or_404(Community, uid=payload.community_uid)
    
    # Generate slug from title
    slug = slugify(payload.title)
    
    # Create mission
    mission = Mission.objects.create(
        slug=slug,
        title=payload.title,
        description=payload.description,
        briefing_time=payload.briefing_time,
        slotting_time=payload.slot_list_time,
        start_time=payload.start_time,
        end_time=payload.end_time,
        visibility=payload.visibility,
        tech_support=payload.tech_support,
        details_map=payload.details_map,
        details_game_mode=payload.details_game_mode,
        required_dlcs=payload.details_required_dlcs,
        game_server=payload.game_server,
        voice_comms=payload.voice_comms,
        repositories=payload.repositories,
        rules=payload.rules_of_engagement,
        creator=user,
        community=community
    )
    
    return {
        'uid': mission.uid,
        'slug': mission.slug,
        'title': mission.title,
        'description': mission.description,
        'briefing_time': mission.briefing_time,
        'slot_list_time': mission.slotting_time,
        'start_time': mission.start_time,
        'end_time': mission.end_time,
        'visibility': mission.visibility,
        'tech_support': mission.tech_support,
        'details_map': mission.details_map,
        'details_game_mode': mission.details_game_mode,
        'details_required_dlcs': mission.required_dlcs,
        'game_server': mission.game_server,
        'voice_comms': mission.voice_comms,
        'repositories': mission.repositories,
        'rules_of_engagement': mission.rules,
        'image_url': mission.image_url,
        'creator': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': None,
            'community': None,
            'active': None
        },
        'community': {
            'uid': community.uid,
            'name': community.name,
            'tag': community.tag,
            'slug': community.slug,
            'website': community.website,
            'image_url': community.image_url,
            'game_servers': community.game_servers,
            'voice_comms': community.voice_comms,
            'repositories': community.repositories
        } if community else None
    }


@router.patch('/{slug}', response=MissionSchema)
def update_mission(request, slug: str, payload: MissionUpdateSchema):
    """Update a mission"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    # Update fields
    if payload.title is not None:
        mission.title = payload.title
    if payload.description is not None:
        mission.description = payload.description
    if payload.briefing_time is not None:
        mission.briefing_time = payload.briefing_time
    if payload.slot_list_time is not None:
        mission.slotting_time = payload.slot_list_time
    if payload.start_time is not None:
        mission.start_time = payload.start_time
    if payload.end_time is not None:
        mission.end_time = payload.end_time
    if payload.visibility is not None:
        mission.visibility = payload.visibility
    if payload.tech_support is not None:
        mission.tech_support = payload.tech_support
    if payload.details_map is not None:
        mission.details_map = payload.details_map
    if payload.details_game_mode is not None:
        mission.details_game_mode = payload.details_game_mode
    if payload.details_required_dlcs is not None:
        mission.required_dlcs = payload.details_required_dlcs
    if payload.game_server is not None:
        mission.game_server = payload.game_server
    if payload.voice_comms is not None:
        mission.voice_comms = payload.voice_comms
    if payload.repositories is not None:
        mission.repositories = payload.repositories
    if payload.rules_of_engagement is not None:
        mission.rules = payload.rules_of_engagement
    
    mission.save()
    
    return {
        'uid': mission.uid,
        'slug': mission.slug,
        'title': mission.title,
        'description': mission.description,
        'briefing_time': mission.briefing_time,
        'slot_list_time': mission.slotting_time,
        'start_time': mission.start_time,
        'end_time': mission.end_time,
        'visibility': mission.visibility,
        'tech_support': mission.tech_support,
        'details_map': mission.details_map,
        'details_game_mode': mission.details_game_mode,
        'details_required_dlcs': mission.required_dlcs,
        'game_server': mission.game_server,
        'voice_comms': mission.voice_comms,
        'repositories': mission.repositories,
        'rules_of_engagement': mission.rules,
        'image_url': mission.image_url,
        'creator': {
            'uid': mission.creator.uid,
            'nickname': mission.creator.nickname,
            'steam_id': None,
            'community': None,
            'active': None
        },
        'community': {
            'uid': mission.community.uid,
            'name': mission.community.name,
            'tag': mission.community.tag,
            'slug': mission.community.slug,
            'website': mission.community.website,
            'image_url': mission.community.image_url,
            'game_servers': mission.community.game_servers,
            'voice_comms': mission.community.voice_comms,
            'repositories': mission.community.repositories
        } if mission.community else None
    }


@router.delete('/{slug}')
def delete_mission(request, slug: str):
    """Delete a mission"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    mission.delete()
    
    return {'success': True}


@router.get('/{slug}/slots', auth=None)
def get_mission_slots(request, slug: str):
    """Get all slots for a mission organized by slot groups"""
    mission = get_object_or_404(Mission.objects.select_related('creator', 'community'), slug=slug)
    
    # Get all slot groups with their slots for this mission
    slot_groups = MissionSlotGroup.objects.filter(mission=mission).prefetch_related(
        'slots__assignee',
        'slots__restricted_community'
    ).order_by('order_number')
    
    result = []
    for slot_group in slot_groups:
        slots = []
        for slot in slot_group.slots.order_by('order_number'):
            slot_data = {
                'uid': str(slot.uid),
                'title': slot.title,
                'description': slot.description,
                'detailedDescription': slot.detailed_description,
                'orderNumber': slot.order_number,
                'requiredDLCs': slot.required_dlcs,
                'externalAssignee': slot.external_assignee,
                'assignee': {
                    'uid': str(slot.assignee.uid),
                    'nickname': slot.assignee.nickname,
                    'steamId': slot.assignee.steam_id,
                } if slot.assignee else None,
                'restrictedCommunity': {
                    'uid': str(slot.restricted_community.uid),
                    'name': slot.restricted_community.name,
                    'tag': slot.restricted_community.tag,
                    'slug': slot.restricted_community.slug,
                } if slot.restricted_community else None
            }
            slots.append(slot_data)
        
        group_data = {
            'uid': str(slot_group.uid),
            'title': slot_group.title,
            'description': slot_group.description,
            'orderNumber': slot_group.order_number,
            'slots': slots
        }
        result.append(group_data)
    
    return result

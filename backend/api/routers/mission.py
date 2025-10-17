from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from datetime import datetime
from django.utils.text import slugify
from api.models import Mission, Community, User
from api.schemas import MissionSchema, MissionCreateSchema, MissionUpdateSchema
from api.auth import has_permission

router = Router()


@router.get('/', response=List[MissionSchema], auth=None)
def list_missions(request, limit: int = 25, offset: int = 0, include_ended: bool = False):
    """List all missions with pagination"""
    query = Mission.objects.select_related('creator', 'community').all()
    
    if not include_ended:
        query = query.filter(end_time__gte=datetime.utcnow()) | query.filter(end_time__isnull=True)
    
    missions = query[offset:offset + limit]
    
    result = []
    for mission in missions:
        result.append({
            'uid': mission.uid,
            'slug': mission.slug,
            'title': mission.title,
            'description': mission.description,
            'briefing_time': mission.briefing_time,
            'slot_list_time': mission.slot_list_time,
            'start_time': mission.start_time,
            'end_time': mission.end_time,
            'visibility': mission.visibility,
            'tech_teleport': mission.tech_teleport,
            'tech_respawn': mission.tech_respawn,
            'details_map': mission.details_map,
            'details_game_mode': mission.details_game_mode,
            'details_required_dlcs': mission.details_required_dlcs,
            'game_server': mission.game_server,
            'voice_comms': mission.voice_comms,
            'repositories': mission.repositories,
            'rules_of_engagement': mission.rules_of_engagement,
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
        'slot_list_time': mission.slot_list_time,
        'start_time': mission.start_time,
        'end_time': mission.end_time,
        'visibility': mission.visibility,
        'tech_teleport': mission.tech_teleport,
        'tech_respawn': mission.tech_respawn,
        'details_map': mission.details_map,
        'details_game_mode': mission.details_game_mode,
        'details_required_dlcs': mission.details_required_dlcs,
        'game_server': mission.game_server,
        'voice_comms': mission.voice_comms,
        'repositories': mission.repositories,
        'rules_of_engagement': mission.rules_of_engagement,
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
        slot_list_time=payload.slot_list_time,
        start_time=payload.start_time,
        end_time=payload.end_time,
        visibility=payload.visibility,
        tech_teleport=payload.tech_teleport,
        tech_respawn=payload.tech_respawn,
        details_map=payload.details_map,
        details_game_mode=payload.details_game_mode,
        details_required_dlcs=payload.details_required_dlcs,
        game_server=payload.game_server,
        voice_comms=payload.voice_comms,
        repositories=payload.repositories,
        rules_of_engagement=payload.rules_of_engagement,
        creator=user,
        community=community
    )
    
    return {
        'uid': mission.uid,
        'slug': mission.slug,
        'title': mission.title,
        'description': mission.description,
        'briefing_time': mission.briefing_time,
        'slot_list_time': mission.slot_list_time,
        'start_time': mission.start_time,
        'end_time': mission.end_time,
        'visibility': mission.visibility,
        'tech_teleport': mission.tech_teleport,
        'tech_respawn': mission.tech_respawn,
        'details_map': mission.details_map,
        'details_game_mode': mission.details_game_mode,
        'details_required_dlcs': mission.details_required_dlcs,
        'game_server': mission.game_server,
        'voice_comms': mission.voice_comms,
        'repositories': mission.repositories,
        'rules_of_engagement': mission.rules_of_engagement,
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
        mission.slot_list_time = payload.slot_list_time
    if payload.start_time is not None:
        mission.start_time = payload.start_time
    if payload.end_time is not None:
        mission.end_time = payload.end_time
    if payload.visibility is not None:
        mission.visibility = payload.visibility
    if payload.tech_teleport is not None:
        mission.tech_teleport = payload.tech_teleport
    if payload.tech_respawn is not None:
        mission.tech_respawn = payload.tech_respawn
    if payload.details_map is not None:
        mission.details_map = payload.details_map
    if payload.details_game_mode is not None:
        mission.details_game_mode = payload.details_game_mode
    if payload.details_required_dlcs is not None:
        mission.details_required_dlcs = payload.details_required_dlcs
    if payload.game_server is not None:
        mission.game_server = payload.game_server
    if payload.voice_comms is not None:
        mission.voice_comms = payload.voice_comms
    if payload.repositories is not None:
        mission.repositories = payload.repositories
    if payload.rules_of_engagement is not None:
        mission.rules_of_engagement = payload.rules_of_engagement
    
    mission.save()
    
    return {
        'uid': mission.uid,
        'slug': mission.slug,
        'title': mission.title,
        'description': mission.description,
        'briefing_time': mission.briefing_time,
        'slot_list_time': mission.slot_list_time,
        'start_time': mission.start_time,
        'end_time': mission.end_time,
        'visibility': mission.visibility,
        'tech_teleport': mission.tech_teleport,
        'tech_respawn': mission.tech_respawn,
        'details_map': mission.details_map,
        'details_game_mode': mission.details_game_mode,
        'details_required_dlcs': mission.details_required_dlcs,
        'game_server': mission.game_server,
        'voice_comms': mission.voice_comms,
        'repositories': mission.repositories,
        'rules_of_engagement': mission.rules_of_engagement,
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

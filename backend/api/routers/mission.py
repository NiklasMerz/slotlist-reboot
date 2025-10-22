from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from datetime import datetime
from django.utils.text import slugify
from api.models import Mission, Community, User, MissionSlotGroup, MissionSlot, ArmaThreeDLC
from api.schemas import MissionSchema, MissionCreateSchema, MissionUpdateSchema
from api.auth import has_permission

router = Router()


def validate_dlc_list(dlc_list, field_name='required_dlcs'):
    """Validate a DLC list and raise error if invalid."""
    # Allow None or empty list
    if not dlc_list:
        return
    
    if not ArmaThreeDLC.validate_dlc_list(dlc_list):
        invalid_dlcs = [dlc for dlc in dlc_list if dlc not in ArmaThreeDLC.get_valid_dlcs()]
        from ninja.errors import HttpError
        raise HttpError(400, f'Invalid {field_name}: {", ".join(invalid_dlcs)}. Valid options: {", ".join(ArmaThreeDLC.get_valid_dlcs())}')


@router.get('/', auth=None)
def list_missions(request, limit: int = 25, offset: int = 0, includeEnded: bool = False, startDate: int = None, endDate: int = None):
    """List all missions with pagination"""
    query = Mission.objects.select_related('creator', 'community').all()
    
    # Date range filtering for calendar
    if startDate and endDate:
        from datetime import datetime as dt, timezone
        start_dt = dt.fromtimestamp(startDate / 1000, tz=timezone.utc)
        end_dt = dt.fromtimestamp(endDate / 1000, tz=timezone.utc)
        query = query.filter(start_time__gte=start_dt, start_time__lte=end_dt)
    elif not includeEnded:
        query = query.filter(end_time__gte=datetime.utcnow()) | query.filter(end_time__isnull=True)
    
    # Get total count before applying pagination
    total = query.count()
    
    # Apply pagination
    missions = query.order_by('-start_time')[offset:offset + limit]
    
    # Get current user if authenticated
    current_user_uid = None
    if hasattr(request, 'auth') and request.auth:
        current_user_uid = request.auth.get('user', {}).get('uid')
    
    # Calculate slot counts for each mission
    result_missions = []
    for mission in missions:
        # Get all slots for this mission
        from django.db.models import Count, Q
        slots = MissionSlot.objects.filter(slot_group__mission=mission)
        
        total_slots = slots.count()
        assigned_slots = slots.filter(assignee__isnull=False).count()
        external_slots = slots.filter(external_assignee__isnull=False).exclude(external_assignee='').count()
        unassigned_slots = slots.filter(assignee__isnull=True, external_assignee__isnull=True).count() + \
                          slots.filter(assignee__isnull=True, external_assignee='').count()
        
        # Open slots are those without assignee, external_assignee, and no restricted community
        open_slots = slots.filter(
            assignee__isnull=True,
            restricted_community__isnull=True
        ).filter(
            Q(external_assignee__isnull=True) | Q(external_assignee='')
        ).count()
        
        # Check if current user is assigned to any slot
        is_assigned_to_any_slot = False
        is_registered_for_any_slot = False
        if current_user_uid:
            is_assigned_to_any_slot = slots.filter(assignee__uid=current_user_uid).exists()
            # Registration status would need to check a separate registration table if it exists
            # For now, keeping it as False
        
        result_missions.append({
            'uid': str(mission.uid),
            'slug': mission.slug,
            'title': mission.title,
            'description': mission.description,
            'briefingTime': mission.briefing_time.isoformat() if mission.briefing_time else None,
            'slottingTime': mission.slotting_time.isoformat() if mission.slotting_time else None,
            'startTime': mission.start_time.isoformat() if mission.start_time else None,
            'endTime': mission.end_time.isoformat() if mission.end_time else None,
            'visibility': mission.visibility,
            'detailsMap': mission.details_map,
            'detailsGameMode': mission.details_game_mode,
            'requiredDLCs': mission.required_dlcs,
            'bannerImageUrl': mission.banner_image_url,
            'slotCounts': {
                'total': total_slots,
                'assigned': assigned_slots,
                'external': external_slots,
                'unassigned': unassigned_slots,
                'open': open_slots
            },
            'isAssignedToAnySlot': is_assigned_to_any_slot,
            'isRegisteredForAnySlot': is_registered_for_any_slot,
            'creator': {
                'uid': str(mission.creator.uid),
                'nickname': mission.creator.nickname,
                'steamId': mission.creator.steam_id,
            },
            'community': {
                'uid': str(mission.community.uid),
                'name': mission.community.name,
                'tag': mission.community.tag,
                'slug': mission.community.slug,
                'website': mission.community.website,
                'logoUrl': mission.community.logo_url,
            } if mission.community else None
        })
    
    return {
        'missions': result_missions,
        'total': total
    }


@router.get('/{slug}', auth=None)
def get_mission(request, slug: str):
    """Get a single mission by slug"""
    mission = get_object_or_404(Mission.objects.select_related('creator', 'community'), slug=slug)
    
    mission_data = {
        'uid': mission.uid,
        'slug': mission.slug,
        'title': mission.title,
        'description': mission.description,
        'briefingTime': mission.briefing_time,
        'slottingTime': mission.slotting_time,
        'startTime': mission.start_time,
        'endTime': mission.end_time,
        'visibility': mission.visibility,
        'techTeleport': bool(mission.tech_support and 'teleport' in mission.tech_support.lower()) if mission.tech_support else False,
        'techRespawn': bool(mission.tech_support and 'respawn' in mission.tech_support.lower()) if mission.tech_support else False,
        'detailsMap': mission.details_map,
        'detailsGameMode': mission.details_game_mode,
        'requiredDLCs': mission.required_dlcs,
        'gameServer': mission.game_server,
        'voiceComms': mission.voice_comms,
        'repositories': mission.repositories,
        'rulesOfEngagement': mission.rules or '',
        'bannerImageUrl': mission.banner_image_url,
        'creator': {
            'uid': mission.creator.uid,
            'nickname': mission.creator.nickname,
            'steamId': mission.creator.steam_id,
        },
        'community': {
            'uid': mission.community.uid,
            'name': mission.community.name,
            'tag': mission.community.tag,
            'slug': mission.community.slug,
            'website': mission.community.website,
            'logoUrl': mission.community.logo_url,
            'gameServers': mission.community.game_servers,
            'voiceComms': mission.community.voice_comms,
            'repositories': mission.community.repositories
        } if mission.community else None
    }
    
    return {'mission': mission_data}


@router.post('/')
def create_mission(request, payload: MissionCreateSchema):
    """Create a new mission"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    # Validate DLCs
    validate_dlc_list(payload.details_required_dlcs, 'details_required_dlcs')
    
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
        'mission': {
            'uid': mission.uid,
            'slug': mission.slug,
            'title': mission.title,
            'description': mission.description,
            'briefingTime': mission.briefing_time,
            'slottingTime': mission.slotting_time,
            'startTime': mission.start_time,
            'endTime': mission.end_time,
            'visibility': mission.visibility,
            'techTeleport': bool(mission.tech_support and 'teleport' in mission.tech_support.lower()) if mission.tech_support else False,
            'techRespawn': bool(mission.tech_support and 'respawn' in mission.tech_support.lower()) if mission.tech_support else False,
            'detailsMap': mission.details_map,
            'detailsGameMode': mission.details_game_mode,
            'requiredDLCs': mission.required_dlcs,
            'gameServer': mission.game_server,
            'voiceComms': mission.voice_comms,
            'repositories': mission.repositories,
            'rulesOfEngagement': mission.rules or '',
            'bannerImageUrl': mission.banner_image_url,
            'creator': {
                'uid': user.uid,
                'nickname': user.nickname,
                'steamId': user.steam_id,
            },
            'community': {
                'uid': community.uid,
                'name': community.name,
                'tag': community.tag,
                'slug': community.slug,
                'website': community.website,
                'logoUrl': community.logo_url,
                'gameServers': community.game_servers,
                'voiceComms': community.voice_comms,
                'repositories': community.repositories
            } if community else None
        }
    }


@router.patch('/{slug}')
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
    
    # Validate DLCs if provided
    if payload.details_required_dlcs is not None:
        validate_dlc_list(payload.details_required_dlcs, 'details_required_dlcs')
    
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
        'mission': {
            'uid': mission.uid,
            'slug': mission.slug,
            'title': mission.title,
            'description': mission.description,
            'briefingTime': mission.briefing_time,
            'slottingTime': mission.slotting_time,
            'startTime': mission.start_time,
            'endTime': mission.end_time,
            'visibility': mission.visibility,
            'techTeleport': bool(mission.tech_support and 'teleport' in mission.tech_support.lower()) if mission.tech_support else False,
            'techRespawn': bool(mission.tech_support and 'respawn' in mission.tech_support.lower()) if mission.tech_support else False,
            'detailsMap': mission.details_map,
            'detailsGameMode': mission.details_game_mode,
            'requiredDLCs': mission.required_dlcs,
            'gameServer': mission.game_server,
            'voiceComms': mission.voice_comms,
            'repositories': mission.repositories,
            'rulesOfEngagement': mission.rules or '',
            'bannerImageUrl': mission.banner_image_url,
            'creator': {
                'uid': mission.creator.uid,
                'nickname': mission.creator.nickname,
                'steamId': mission.creator.steam_id,
            },
            'community': {
                'uid': mission.community.uid,
                'name': mission.community.name,
                'tag': mission.community.tag,
                'slug': mission.community.slug,
                'website': mission.community.website,
                'logoUrl': mission.community.logo_url,
                'gameServers': mission.community.game_servers,
                'voiceComms': mission.community.voice_comms,
                'repositories': mission.community.repositories
            } if mission.community else None
        }
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
    
    return {'slotGroups': result}

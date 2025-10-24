from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from django.utils.text import slugify
from pydantic import BaseModel
from api.models import Mission, Community, User, MissionSlotGroup, MissionSlot, ArmaThreeDLC, MissionSlotRegistration
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
    # When startDate and endDate are provided (calendar view), return just array
    is_calendar_query = startDate is not None and endDate is not None
    
    if is_calendar_query:
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
    
    # Calendar queries return just the array for backwards compatibility
    if is_calendar_query:
        return result_missions
    
    return {
        'missions': result_missions,
        'total': total
    }


@router.get('/slugAvailable', auth=None)
def check_slug_availability(request, slug: str):
    """Check if a mission slug is available"""
    # Check if a mission with this slug already exists
    exists = Mission.objects.filter(slug=slug).exists()
    
    return {
        'available': not exists
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
    
    # Convert tech_teleport and tech_respawn to tech_support string
    tech_support_parts = []
    if payload.tech_teleport:
        tech_support_parts.append('teleport')
    if payload.tech_respawn:
        tech_support_parts.append('respawn')
    tech_support = ', '.join(tech_support_parts) if tech_support_parts else None
    
    # Use default datetime for required fields if not provided
    # This matches the original TypeScript backend behavior
    from datetime import datetime, timezone
    default_time = datetime.now(timezone.utc)
    
    # Create mission
    mission = Mission.objects.create(
        slug=slug,
        title=payload.title,
        description=payload.description,
        short_description=payload.description or '',
        detailed_description='',
        briefing_time=payload.briefing_time or default_time,
        slotting_time=payload.slot_list_time or default_time,
        start_time=payload.start_time or default_time,
        end_time=payload.end_time or default_time,
        visibility=payload.visibility,
        tech_support=tech_support,
        details_map=payload.details_map,
        details_game_mode=payload.details_game_mode,
        required_dlcs=payload.details_required_dlcs if payload.details_required_dlcs is not None else [],
        game_server=payload.game_server,
        voice_comms=payload.voice_comms,
        repositories=payload.repositories if payload.repositories is not None else [],
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
    
    # Handle tech_teleport and tech_respawn conversion to tech_support
    if payload.tech_teleport is not None or payload.tech_respawn is not None:
        # Get current tech_support settings
        current_teleport = mission.tech_support and 'teleport' in mission.tech_support.lower() if mission.tech_support else False
        current_respawn = mission.tech_support and 'respawn' in mission.tech_support.lower() if mission.tech_support else False
        
        # Update with new values if provided
        new_teleport = payload.tech_teleport if payload.tech_teleport is not None else current_teleport
        new_respawn = payload.tech_respawn if payload.tech_respawn is not None else current_respawn
        
        # Build new tech_support string
        tech_support_parts = []
        if new_teleport:
            tech_support_parts.append('teleport')
        if new_respawn:
            tech_support_parts.append('respawn')
        mission.tech_support = ', '.join(tech_support_parts) if tech_support_parts else None
    
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
        'slots__restricted_community',
        'slots__registrations'
    ).order_by('order_number')
    
    result = []
    for slot_group in slot_groups:
        slots = []
        for slot in slot_group.slots.order_by('order_number'):
            # Count pending registrations for this slot
            registration_count = slot.registrations.count()
            
            slot_data = {
                'uid': str(slot.uid),
                'title': slot.title,
                'description': slot.description,
                'detailedDescription': slot.detailed_description,
                'orderNumber': slot.order_number,
                'requiredDLCs': slot.required_dlcs,
                'externalAssignee': slot.external_assignee,
                'registrationCount': registration_count,
                'blocked': slot.blocked,
                'reserve': slot.reserve,
                'autoAssignable': slot.auto_assignable,
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


# Slot Registration Schemas
class SlotRegistrationCreateSchema(BaseModel):
    comment: Optional[str] = None


class SlotRegistrationUpdateSchema(BaseModel):
    confirmed: bool
    suppressNotifications: Optional[bool] = False


@router.get('/{slug}/slots/{slot_uid}/registrations')
def get_slot_registrations(request, slug: str, slot_uid: UUID, limit: int = 10, offset: int = 0):
    """Get all registrations for a specific mission slot"""
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    
    total = MissionSlotRegistration.objects.filter(slot=slot).count()
    registrations = MissionSlotRegistration.objects.filter(slot=slot).select_related('user')[offset:offset + limit]
    
    return {
        'registrations': [
            {
                'uid': str(reg.uid),
                'slotUid': str(reg.slot.uid),
                'user': {
                    'uid': str(reg.user.uid),
                    'nickname': reg.user.nickname,
                    'steamId': reg.user.steam_id,
                },
                'comment': reg.comment,
                'confirmed': False,  # All existing registrations are pending (not confirmed)
                'createdAt': reg.created_at.isoformat() if reg.created_at else None,
            }
            for reg in registrations
        ],
        'limit': limit,
        'offset': offset,
        'total': total
    }


@router.post('/{slug}/slots/{slot_uid}/registrations', response={200: dict, 400: dict, 403: dict})
def register_for_slot(request, slug: str, slot_uid: UUID, data: SlotRegistrationCreateSchema):
    """Register the authenticated user for a mission slot"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    
    # Check if user is already registered
    existing = MissionSlotRegistration.objects.filter(user=user, slot=slot).first()
    if existing:
        return 400, {'detail': 'User already registered for this slot'}
    
    # Create registration
    registration = MissionSlotRegistration.objects.create(
        user=user,
        slot=slot,
        comment=data.comment
    )
    
    return {
        'registration': {
            'uid': str(registration.uid),
            'slotUid': str(slot.uid),
            'user': {
                'uid': str(user.uid),
                'nickname': user.nickname,
                'steamId': user.steam_id,
            },
            'comment': registration.comment,
            'confirmed': False,  # New registrations are pending
            'createdAt': registration.created_at.isoformat() if registration.created_at else None,
        }
    }


@router.patch('/{slug}/slots/{slot_uid}/registrations/{registration_uid}', response={200: dict, 400: dict, 403: dict})
def update_slot_registration(request, slug: str, slot_uid: UUID, registration_uid: UUID, data: SlotRegistrationUpdateSchema):
    """Update/confirm a slot registration (requires permissions)"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    permissions = request.auth.get('permissions', [])
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    registration = get_object_or_404(MissionSlotRegistration, uid=registration_uid, slot=slot)

    
    # Check permissions - user must be mission creator or have appropriate permissions
    is_creator = str(mission.creator.uid) == str(user.uid)
    has_perm = has_permission(permissions, ['mission.slot.assign', 'admin.*'])
    
    if not is_creator and not has_perm:
        return 403, {'detail': 'Insufficient permissions to confirm registration'}
    
    # If confirmed, assign the slot to the user
    if data.confirmed:
        # Check if slot is already assigned
        if slot.assignee:
            return 400, {'detail': 'Slot is already assigned'}
        
        # Store registration info before deletion
        registration_user = registration.user
        registration_uid_str = str(registration.uid)
        registration_comment = registration.comment
        
        slot.assignee = registration_user
        slot.save()
        
        # Delete the registration after confirming
        registration.delete()
        
        return {
            'registration': {
                'uid': registration_uid_str,
                'user': {
                    'uid': str(registration_user.uid),
                    'nickname': registration_user.nickname,
                    'steamId': registration_user.steam_id,
                },
                'comment': registration_comment,
                'confirmed': True
            }
        }
    
    return {
        'registration': {
            'uid': str(registration.uid),
            'user': {
                'uid': str(registration.user.uid),
                'nickname': registration.user.nickname,
                'steamId': registration.user.steam_id,
            },
            'comment': registration.comment,
            'confirmed': False
        }
    }


@router.delete('/{slug}/slots/{slot_uid}/registrations/{registration_uid}', response={200: dict, 403: dict})
def delete_slot_registration(request, slug: str, slot_uid: UUID, registration_uid: UUID):
    """Delete/unregister from a slot"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    permissions = request.auth.get('permissions', [])
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    registration = get_object_or_404(MissionSlotRegistration, uid=registration_uid, slot=slot)
    
    # User can delete their own registration, or mission creator/admin can delete any
    is_own_registration = str(registration.user.uid) == str(user.uid)
    is_creator = str(mission.creator.uid) == str(user.uid)
    has_perm = has_permission(permissions, ['mission.slot.assign', 'admin.*'])
    
    if not is_own_registration and not is_creator and not has_perm:
        return 403, {'detail': 'Insufficient permissions to delete this registration'}
    
    registration.delete()
    
    return {'success': True}


@router.post('/{slug}/slots/{slot_uid}/unassign', response={200: dict, 400: dict, 403: dict})
def unassign_slot(request, slug: str, slot_uid: UUID):
    """Unassign a user from a mission slot"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    permissions = request.auth.get('permissions', [])
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    
    if not slot.assignee:
        return 400, {'detail': 'Slot is not assigned'}
    
    # Check permissions - user must be the assignee, mission creator, or have appropriate permissions
    is_assignee = str(slot.assignee.uid) == str(user.uid)
    is_creator = str(mission.creator.uid) == str(user.uid)
    has_perm = has_permission(permissions, ['mission.slot.assign', 'admin.*'])
    
    if not is_assignee and not is_creator and not has_perm:
        return 403, {'detail': 'Insufficient permissions to unassign this slot'}
    
    slot.assignee = None
    slot.save()
    
    return {
        'slot': {
            'uid': str(slot.uid),
            'title': slot.title,
            'assignee': None
        }
    }




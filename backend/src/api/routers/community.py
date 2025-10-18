from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from django.utils.text import slugify
from api.models import Community
from api.schemas import CommunitySchema, CommunityCreateSchema, CommunityUpdateSchema
from api.auth import has_permission

router = Router()


@router.get('/', response=List[CommunitySchema], auth=None)
def list_communities(request, limit: int = 25, offset: int = 0):
    """List all communities with pagination"""
    communities = Community.objects.all()[offset:offset + limit]
    return [
        {
            'uid': community.uid,
            'name': community.name,
            'tag': community.tag,
            'slug': community.slug,
            'website': community.website,
            'image_url': community.image_url,
            'game_servers': community.game_servers,
            'voice_comms': community.voice_comms,
            'repositories': community.repositories
        }
        for community in communities
    ]


@router.get('/{slug}', response=CommunitySchema, auth=None)
def get_community(request, slug: str):
    """Get a single community by slug"""
    community = get_object_or_404(Community, slug=slug)
    
    return {
        'uid': community.uid,
        'name': community.name,
        'tag': community.tag,
        'slug': community.slug,
        'website': community.website,
        'image_url': community.image_url,
        'game_servers': community.game_servers,
        'voice_comms': community.voice_comms,
        'repositories': community.repositories
    }


@router.post('/', response=CommunitySchema)
def create_community(request, payload: CommunityCreateSchema):
    """Create a new community"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    # Generate slug from name
    slug = slugify(payload.name)
    
    community = Community.objects.create(
        name=payload.name,
        tag=payload.tag,
        slug=slug,
        website=payload.website,
        game_servers=payload.game_servers,
        voice_comms=payload.voice_comms,
        repositories=payload.repositories
    )
    
    return {
        'uid': community.uid,
        'name': community.name,
        'tag': community.tag,
        'slug': community.slug,
        'website': community.website,
        'image_url': community.image_url,
        'game_servers': community.game_servers,
        'voice_comms': community.voice_comms,
        'repositories': community.repositories
    }


@router.patch('/{slug}', response=CommunitySchema)
def update_community(request, slug: str, payload: CommunityUpdateSchema):
    """Update a community"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    
    if payload.name is not None:
        community.name = payload.name
    if payload.tag is not None:
        community.tag = payload.tag
    if payload.website is not None:
        community.website = payload.website
    if payload.game_servers is not None:
        community.game_servers = payload.game_servers
    if payload.voice_comms is not None:
        community.voice_comms = payload.voice_comms
    if payload.repositories is not None:
        community.repositories = payload.repositories
    
    community.save()
    
    return {
        'uid': community.uid,
        'name': community.name,
        'tag': community.tag,
        'slug': community.slug,
        'website': community.website,
        'image_url': community.image_url,
        'game_servers': community.game_servers,
        'voice_comms': community.voice_comms,
        'repositories': community.repositories
    }


@router.delete('/{slug}')
def delete_community(request, slug: str):
    """Delete a community"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    community.delete()
    
    return {'success': True}

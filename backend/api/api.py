from ninja import NinjaAPI
from ninja.security import HttpBearer
from typing import Optional
from api.auth import decode_jwt
from django.http import HttpRequest


class JWTAuth(HttpBearer):
    """JWT Authentication for Django Ninja"""
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[dict]:
        """
        Authenticate the request using JWT token.
        Supports both 'Bearer <token>' and 'JWT <token>' formats.
        """
        # The token parameter already has the 'Bearer ' prefix stripped by HttpBearer
        # But if the client sent 'JWT <token>', we need to handle that
        auth_header = request.headers.get('Authorization', '')
        
        # Extract token from header, supporting both JWT and Bearer prefixes
        if auth_header.startswith('JWT '):
            token = auth_header[4:]  # Remove 'JWT ' prefix
        elif auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Decode and verify the token
        payload = decode_jwt(token)
        if payload:
            return payload
        
        print(f"JWT authentication failed for token: {token[:50]}...")
        return None


# Create API instance
api = NinjaAPI(
    title='slotlist.online API',
    version='2.0.0',
    description='Backend API for slotlist.online - ArmA 3 mission planning and slotlist management',
    auth=JWTAuth()
)

# Import routers after API is created to avoid circular imports
from api.routers import auth, mission, user, community, status, notification, mission_slot_template

# Register routers
api.add_router('/v1/auth/', auth.router, tags=['Authentication'], auth=None)
api.add_router('/v1/missions/', mission.router, tags=['Missions'])
api.add_router('/v1/missionSlotTemplates/', mission_slot_template.router, tags=['Mission Slot Templates'])
api.add_router('/v1/users/', user.router, tags=['Users'])
api.add_router('/v1/communities/', community.router, tags=['Communities'])
api.add_router('/v1/notifications/', notification.router, tags=['Notifications'])
api.add_router('/v1/', status.router, tags=['Status'])

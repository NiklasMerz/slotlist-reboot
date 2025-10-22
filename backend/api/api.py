from ninja import NinjaAPI
from ninja.security import HttpBearer
from typing import Optional
from api.auth import decode_jwt
from django.http import HttpRequest


class JWTAuth(HttpBearer):
    """JWT Authentication for Django Ninja that supports both JWT and Bearer prefixes"""
    
    openapi_scheme: str = "bearer"
    
    def __call__(self, request: HttpRequest) -> Optional[dict]:
        """
        Override __call__ to handle JWT prefix in addition to Bearer.
        This is called before authenticate() to extract the token from headers.
        """
        auth_header = request.headers.get('Authorization', '')
        
        # Handle JWT prefix (legacy format)
        if auth_header.startswith('JWT '):
            token = auth_header[4:].strip()
            return self.authenticate(request, token)
        
        # Handle Bearer prefix (standard format)
        elif auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
            return self.authenticate(request, token)
        
        return None
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[dict]:
        """
        Authenticate the request using JWT token.
        """
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

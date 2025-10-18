from ninja import NinjaAPI
from ninja.security import HttpBearer
from typing import Optional
from api.auth import decode_jwt
from django.http import HttpRequest


class JWTAuth(HttpBearer):
    """JWT Authentication for Django Ninja"""
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[dict]:
        payload = decode_jwt(token)
        if payload:
            return payload
        return None


# Create API instance
api = NinjaAPI(
    title='slotlist.info API',
    version='2.0.0',
    description='Backend API for slotlist.info - ArmA 3 mission planning and slotlist management',
    auth=JWTAuth()
)

# Import routers after API is created to avoid circular imports
from api.routers import auth, mission, user, community, status, notification

# Register routers
api.add_router('/v1/auth/', auth.router, tags=['Authentication'], auth=None)
api.add_router('/v1/missions/', mission.router, tags=['Missions'])
api.add_router('/v1/users/', user.router, tags=['Users'])
api.add_router('/v1/communities/', community.router, tags=['Communities'])
api.add_router('/v1/notifications/', notification.router, tags=['Notifications'])
api.add_router('/v1/', status.router, tags=['Status'])

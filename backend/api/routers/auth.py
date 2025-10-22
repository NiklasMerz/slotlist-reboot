from ninja import Router
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User as DjangoUser
from api.models import User
from api.schemas import AuthResponseSchema, UserSchema, ErrorResponseSchema
from api.auth import generate_jwt, get_or_create_user_from_django_user
from api.steam_auth import steam_service
from pydantic import BaseModel

router = Router()


class DevLoginSchema(BaseModel):
    nickname: str
    steam_id: str = None


class DjangoLoginSchema(BaseModel):
    username: str
    password: str


class SteamLoginSchema(BaseModel):
    url: str


@router.get('/steam', auth=None)
def get_steam_login_url(request):
    """
    Get Steam OpenID login URL
    
    Returns the URL to redirect the user to for Steam authentication.
    The frontend should redirect the user to this URL to begin the Steam login process.
    
    **Authentication:** None required
    
    **Returns:**
    - `url` (str): Steam OpenID URL to redirect user to for authentication
    
    **Example Response:**
    ```json
    {
        "url": "https://steamcommunity.com/openid/login?openid.ns=..."
    }
    ```
    """
    # Get the return URL from frontend (where Steam should redirect after auth)
    # In production, this should be configured based on your frontend URL
    frontend_url = request.GET.get('return_url', settings.JWT_ISSUER)
    realm = settings.JWT_ISSUER
    
    login_url = steam_service.get_login_url(frontend_url, realm)
    
    return {'url': login_url}


@router.post('/steam', response={200: AuthResponseSchema, 400: ErrorResponseSchema, 403: ErrorResponseSchema}, auth=None)
def verify_steam_login(request, payload: SteamLoginSchema):
    """
    Verify Steam OpenID authentication and return JWT
    
    After Steam redirects the user back to your frontend with OpenID parameters,
    send the full callback URL to this endpoint to verify the authentication and
    receive a JWT token.
    
    **Authentication:** None required
    
    **Request Body:**
    - `url` (str): Full callback URL with OpenID parameters from Steam
    
    **Returns:**
    - `token` (str): JWT token for authenticated user
    - `user` (object): User information
    
    **Example Request:**
    ```json
    {
        "url": "https://yoursite.com/auth/callback?openid.ns=..."
    }
    ```
    
    **Example Response:**
    ```json
    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "uid": "123e4567-e89b-12d3-a456-426614174000",
            "nickname": "PlayerName",
            "steam_id": "76561198...",
            "active": true
        }
    }
    ```
    
    **Errors:**
    - `400`: Invalid OpenID response
    - `403`: User account is deactivated
    """
    # Extract return URL from the openid response
    return_url = request.GET.get('return_url', settings.JWT_ISSUER)
    
    # Verify Steam login and get Steam ID
    steam_id = steam_service.verify_and_get_steam_id(payload.url, return_url)
    
    if not steam_id:
        return 400, {'detail': 'Invalid Steam OpenID response'}
    
    # Get or create user
    try:
        user = User.objects.get(steam_id=steam_id)
        
        # Check if user is active
        if not user.active:
            return 403, {'detail': 'User account is deactivated'}
            
    except User.DoesNotExist:
        # Get user info from Steam API
        steam_info = steam_service.get_steam_user_info(steam_id)
        
        # Create new user
        user = User.objects.create(
            steam_id=steam_id,
            nickname=steam_info['nickname'],
            active=True
        )
    
    # Generate JWT
    token = generate_jwt(user)
    
    return {
        'token': token,
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': None,
            'active': user.active
        }
    }


@router.post('/dev-login', response=AuthResponseSchema, auth=None)
def dev_login(request, credentials: DevLoginSchema):
    """
    Development-only login endpoint that bypasses Steam authentication
    
    **⚠️ WARNING: Only enabled when DEBUG=True. Never use in production!**
    
    This endpoint allows testing authentication flow without Steam OAuth.
    It creates or logs in a user with the provided credentials.
    
    **Authentication:** None required
    
    **Request Body:**
    - `nickname` (str): User nickname
    - `steam_id` (str, optional): Steam ID (auto-generated if not provided)
    
    **Returns:**
    - `token` (str): JWT token for authenticated user
    - `user` (object): User information
    
    **Example Request:**
    ```json
    {
        "nickname": "TestUser",
        "steam_id": "76561198000000000"
    }
    ```
    
    **Errors:**
    - `403`: Development login disabled (production mode)
    - `400`: Invalid request data
    """
    # Only allow in development mode
    if not settings.DEBUG:
        return 403, {'detail': 'Development login is only available in DEBUG mode'}
    
    # Generate a fake Steam ID if not provided
    steam_id = credentials.steam_id
    if not steam_id:
        # Generate a fake Steam ID starting with 76561198 (common Steam ID prefix)
        import random
        steam_id = f"76561198{random.randint(100000000, 999999999)}"
    
    # Get or create user
    user, created = User.objects.get_or_create(
        steam_id=steam_id,
        defaults={
            'nickname': credentials.nickname,
            'active': True
        }
    )
    
    # Update nickname if user already exists
    if not created and user.nickname != credentials.nickname:
        user.nickname = credentials.nickname
        user.save()
    
    # Check if user is active
    if not user.active:
        return 403, {'detail': 'User account is deactivated'}
    
    # Generate JWT
    token = generate_jwt(user)
    
    return {
        'token': token,
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug
            } if user.community else None,
            'active': user.active
        }
    }


@router.post('/django-login', response=AuthResponseSchema, auth=None)
def django_login(request, credentials: DjangoLoginSchema):
    """
    Django username/password authentication endpoint
    
    **Only available in development mode (DEBUG=True)**
    
    Authenticates against Django's built-in user system and creates
    corresponding User records in the slotlist system.
    
    **Authentication:** None required
    
    **Request Body:**
    - `username` (str): Django username
    - `password` (str): Django password
    
    **Returns:**
    - `token` (str): JWT token for authenticated user
    - `user` (object): User information
    
    **Example Request:**
    ```json
    {
        "username": "admin",
        "password": "password123"
    }
    ```
    
    **Errors:**
    - `403`: Django login disabled (production mode)
    - `401`: Invalid credentials
    - `403`: User account is deactivated
    """
    # Only allow in development mode
    if not settings.DEBUG:
        return 403, {'detail': 'Django login is only available in DEBUG mode'}
    
    # Authenticate against Django users
    django_user = authenticate(
        request=request,
        username=credentials.username,
        password=credentials.password
    )
    
    if not django_user:
        return 401, {'detail': 'Invalid credentials'}
    
    if not django_user.is_active:
        return 403, {'detail': 'User account is deactivated'}
    
    # Get or create corresponding User record
    user = get_or_create_user_from_django_user(django_user)
    
    # Generate JWT
    token = generate_jwt(user)
    
    return {
        'token': token,
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug
            } if user.community else None,
            'active': user.active
        }
    }


@router.post('/refresh', response=AuthResponseSchema)
def refresh_token(request):
    """
    Refresh JWT token
    
    Generates a new JWT token for the authenticated user with updated permissions
    and user information. Should be called after any user profile changes.
    
    **Authentication:** Required (JWT)
    
    **Returns:**
    - `token` (str): New JWT token
    - `user` (object): Updated user information
    
    **Example Response:**
    ```json
    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "uid": "123e4567-e89b-12d3-a456-426614174000",
            "nickname": "PlayerName",
            "steam_id": "76561198...",
            "active": true
        }
    }
    ```
    
    **Errors:**
    - `401`: Invalid or expired token
    - `403`: User account is deactivated
    """
    user_data = request.auth.get('user')
    if not user_data:
        return 401, {'detail': 'Invalid token'}
    
    user = get_object_or_404(User, uid=user_data['uid'])
    
    if not user.active:
        return 403, {'detail': 'User account is deactivated'}
    
    token = generate_jwt(user)
    
    return {
        'token': token,
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': None,
            'active': user.active
        }
    }


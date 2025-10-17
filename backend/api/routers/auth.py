from ninja import Router
from django.shortcuts import get_object_or_404
from django.conf import settings
from api.models import User
from api.schemas import AuthResponseSchema, UserSchema
from api.auth import generate_jwt
from api.steam_auth import steam_service

router = Router()


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


@router.post('/steam', response=AuthResponseSchema, auth=None)
def verify_steam_login(request, url: str):
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
    steam_id = steam_service.verify_and_get_steam_id(url, return_url)
    
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


"""
Steam OpenID Authentication Service

This module provides Steam OpenID authentication functionality for Django.
It handles the Steam login flow, verification, and retrieving user information from Steam API.
"""

import re
import requests
from typing import Optional, Dict, Any
from django.conf import settings


class SteamOpenIDService:
    """Service for Steam OpenID authentication"""
    
    STEAM_OPENID_URL = 'https://steamcommunity.com/openid'
    STEAM_API_URL = 'https://api.steampowered.com'
    
    def __init__(self):
        self.steam_api_key = settings.STEAM_API_SECRET
    
    def get_login_url(self, return_url: str, realm: str) -> str:
        """
        Generate Steam OpenID login URL
        
        Args:
            return_url: URL where Steam should redirect after authentication
            realm: OpenID realm (usually your domain)
            
        Returns:
            str: Steam OpenID login URL to redirect user to
        """
        from urllib.parse import urlencode
        
        # Build OpenID parameters manually to avoid association issues
        params = {
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.mode': 'checkid_setup',
            'openid.return_to': return_url,
            'openid.realm': realm,
            'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
        }
        
        return f'{self.STEAM_OPENID_URL}/login?{urlencode(params)}'
    
    def verify_and_get_steam_id(self, openid_url: str, return_url: str) -> Optional[str]:
        """
        Verify Steam OpenID response and extract Steam ID
        
        Args:
            openid_url: The full URL with OpenID parameters from Steam callback
            return_url: The return URL used in the initial request
            
        Returns:
            str: Steam ID if verification successful, None otherwise
        """
        # Parse the OpenID response from URL parameters
        params = self._parse_openid_params(openid_url)
        
        # Debug logging
        print(f"Parsed OpenID params: {list(params.keys())}")
        print(f"Has claimed_id: {'openid.claimed_id' in params}")
        
        # Steam uses stateless mode, so we verify directly without association
        # Check required OpenID parameters
        if 'openid.claimed_id' not in params:
            print(f"Missing openid.claimed_id in params")
            return None
            
        # Verify the response with Steam
        if not self._verify_openid_response(params):
            print(f"OpenID verification failed with Steam")
            return None
        
        # Extract Steam ID from claimed identifier
        # Format: https://steamcommunity.com/openid/id/<STEAM_ID>
        claimed_id = params.get('openid.claimed_id', '')
        print(f"Claimed ID: {claimed_id}")
        steam_id_match = re.match(r'https?://steamcommunity\.com/openid/id/(\d+)', claimed_id)
        
        if steam_id_match:
            steam_id = steam_id_match.group(1)
            print(f"Extracted Steam ID: {steam_id}")
            return steam_id
        
        print(f"Could not extract Steam ID from claimed_id")
        return None
    
    def _verify_openid_response(self, params: Dict[str, str]) -> bool:
        """
        Verify OpenID response directly with Steam
        
        Args:
            params: OpenID parameters from callback
            
        Returns:
            bool: True if verification successful
        """
        # Change mode to check_authentication for verification
        verify_params = params.copy()
        verify_params['openid.mode'] = 'check_authentication'
        
        try:
            print(f"Verifying with Steam: {self.STEAM_OPENID_URL}")
            response = requests.post(self.STEAM_OPENID_URL, data=verify_params, timeout=10)
            response.raise_for_status()
            
            # Check if Steam confirms the authentication
            content = response.text
            print(f"Steam verification response: {content[:200]}")
            is_valid = 'is_valid:true' in content
            print(f"Verification result: {is_valid}")
            return is_valid
        except Exception as e:
            print(f"OpenID verification failed: {e}")
            return False
    
    def get_steam_user_info(self, steam_id: str) -> Dict[str, Any]:
        """
        Retrieve user information from Steam API
        
        Args:
            steam_id: Steam ID of the user
            
        Returns:
            dict: User information including nickname (personaname)
        """
        url = f'{self.STEAM_API_URL}/ISteamUser/GetPlayerSummaries/v0002/'
        
        params = {
            'key': self.steam_api_key,
            'steamids': steam_id,
            'format': 'json'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'response' in data and 'players' in data['response'] and len(data['response']['players']) > 0:
            player = data['response']['players'][0]
            return {
                'steam_id': steam_id,
                'nickname': player.get('personaname', f'User{steam_id[-6:]}'),
                'avatar': player.get('avatarfull', player.get('avatarmedium', player.get('avatar'))),
                'profile_url': player.get('profileurl')
            }
        
        # Fallback if API fails
        return {
            'steam_id': steam_id,
            'nickname': f'User{steam_id[-6:]}',
            'avatar': None,
            'profile_url': None
        }
    
    def _parse_openid_params(self, url: str) -> Dict[str, str]:
        """
        Parse OpenID parameters from URL
        
        Args:
            url: Full URL with query parameters
            
        Returns:
            dict: Parsed OpenID parameters
        """
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Convert lists to single values
        return {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in params.items()}


# Singleton instance
steam_service = SteamOpenIDService()

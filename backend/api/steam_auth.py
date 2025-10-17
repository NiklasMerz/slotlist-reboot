"""
Steam OpenID Authentication Service

This module provides Steam OpenID authentication functionality for Django.
It handles the Steam login flow, verification, and retrieving user information from Steam API.
"""

import re
import requests
from typing import Optional, Dict, Any
from django.conf import settings
from openid.consumer import consumer
from openid.extensions import sreg
from openid.store.memstore import MemoryStore


class SteamOpenIDService:
    """Service for Steam OpenID authentication"""
    
    STEAM_OPENID_URL = 'https://steamcommunity.com/openid'
    STEAM_API_URL = 'https://api.steampowered.com'
    
    def __init__(self):
        self.store = MemoryStore()
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
        openid_consumer = consumer.Consumer({}, self.store)
        
        # Begin authentication process
        auth_request = openid_consumer.begin(self.STEAM_OPENID_URL)
        
        # Add simple registration extension
        sreg_request = sreg.SRegRequest(required=['nickname'])
        auth_request.addExtension(sreg_request)
        
        # Generate redirect URL
        redirect_url = auth_request.redirectURL(realm, return_url)
        
        return redirect_url
    
    def verify_and_get_steam_id(self, openid_url: str, return_url: str) -> Optional[str]:
        """
        Verify Steam OpenID response and extract Steam ID
        
        Args:
            openid_url: The full URL with OpenID parameters from Steam callback
            return_url: The return URL used in the initial request
            
        Returns:
            str: Steam ID if verification successful, None otherwise
        """
        openid_consumer = consumer.Consumer({}, self.store)
        
        # Parse the OpenID response from URL parameters
        params = self._parse_openid_params(openid_url)
        
        # Complete authentication
        auth_response = openid_consumer.complete(params, return_url)
        
        if auth_response.status == consumer.SUCCESS:
            # Extract Steam ID from claimed identifier
            # Format: https://steamcommunity.com/openid/id/<STEAM_ID>
            claimed_id = auth_response.identity_url
            steam_id_match = re.match(r'https?://steamcommunity\.com/openid/id/(\d+)', claimed_id)
            
            if steam_id_match:
                return steam_id_match.group(1)
        
        return None
    
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

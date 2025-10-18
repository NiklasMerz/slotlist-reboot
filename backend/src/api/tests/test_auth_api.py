"""
API Compatibility Tests for Authentication Endpoints

Tests that verify the Django Ninja API behaves exactly like the legacy TypeScript/Hapi.js API
for all authentication-related endpoints.
"""

from django.test import TestCase, Client
from django.urls import reverse
from api.models import User, Permission, Community
import json
import jwt
import time
from django.conf import settings


class AuthAPICompatibilityTests(TestCase):
    """Test authentication endpoints for compatibility with legacy API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.test_user = User.objects.create(
            uid='test-user-uid-1234',
            steamId='76561198012345678',
            nickname='TestUser',
            active=True
        )
        
        # Create test JWT token
        self.test_token = jwt.encode(
            {
                'uid': self.test_user.uid,
                'nickname': self.test_user.nickname,
                'steamId': self.test_user.steamId,
                'permissions': [],
                'iat': int(time.time()),
                'exp': int(time.time()) + settings.JWT_EXPIRES_IN
            },
            settings.JWT_SECRET,
            algorithm='HS256'
        )
    
    def test_get_steam_login_url(self):
        """Test GET /api/v1/auth/steam - Returns Steam OpenID redirect URL"""
        response = self.client.get('/api/v1/auth/steam')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain URL
        data = response.json()
        self.assertIn('url', data)
        self.assertTrue(data['url'].startswith('https://steamcommunity.com/openid/login'))
        
    def test_post_steam_login_invalid_url(self):
        """Test POST /api/v1/auth/steam with invalid URL - Should return 400"""
        response = self.client.post(
            '/api/v1/auth/steam',
            data=json.dumps({'url': 'invalid-url'}),
            content_type='application/json'
        )
        
        # Should return 400 or 401 for invalid Steam response
        self.assertIn(response.status_code, [400, 401])
    
    def test_refresh_jwt_authenticated(self):
        """Test POST /api/v1/auth/refresh - Refreshes JWT with valid token"""
        response = self.client.post(
            '/api/v1/auth/refresh',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain new token
        data = response.json()
        self.assertIn('token', data)
        self.assertTrue(len(data['token']) > 0)
        
    def test_refresh_jwt_unauthenticated(self):
        """Test POST /api/v1/auth/refresh without token - Should return 401"""
        response = self.client.post('/api/v1/auth/refresh')
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)
    
    def test_refresh_jwt_invalid_token(self):
        """Test POST /api/v1/auth/refresh with invalid token - Should return 401"""
        response = self.client.post(
            '/api/v1/auth/refresh',
            HTTP_AUTHORIZATION='Bearer invalid-token'
        )
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)
    
    def test_refresh_jwt_deactivated_user(self):
        """Test POST /api/v1/auth/refresh with deactivated user - Should return 403"""
        # Deactivate user
        self.test_user.active = False
        self.test_user.save()
        
        response = self.client.post(
            '/api/v1/auth/refresh',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Reactivate for cleanup
        self.test_user.active = True
        self.test_user.save()
    
    def test_get_account_details_authenticated(self):
        """Test GET /api/v1/auth/account - Returns user account details"""
        response = self.client.get(
            '/api/v1/auth/account',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain user details
        data = response.json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['uid'], self.test_user.uid)
        self.assertEqual(data['user']['nickname'], self.test_user.nickname)
        self.assertEqual(data['user']['steamId'], self.test_user.steamId)
    
    def test_get_account_details_unauthenticated(self):
        """Test GET /api/v1/auth/account without token - Should return 401"""
        response = self.client.get('/api/v1/auth/account')
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)
    
    def test_patch_account_details_update_nickname(self):
        """Test PATCH /api/v1/auth/account - Updates user nickname"""
        new_nickname = 'UpdatedNickname'
        
        response = self.client.patch(
            '/api/v1/auth/account',
            data=json.dumps({'nickname': new_nickname}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain updated user and new token
        data = response.json()
        self.assertIn('user', data)
        self.assertIn('token', data)
        self.assertEqual(data['user']['nickname'], new_nickname)
        
        # Verify in database
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.nickname, new_nickname)
    
    def test_patch_account_details_unauthenticated(self):
        """Test PATCH /api/v1/auth/account without token - Should return 401"""
        response = self.client.patch(
            '/api/v1/auth/account',
            data=json.dumps({'nickname': 'NewNickname'}),
            content_type='application/json'
        )
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)
    
    def test_delete_account_with_correct_nickname(self):
        """Test POST /api/v1/auth/account/delete - Deletes account with correct nickname"""
        # Create a separate user for deletion
        delete_user = User.objects.create(
            uid='delete-user-uid',
            steamId='76561198087654321',
            nickname='DeleteUser',
            active=True
        )
        
        delete_token = jwt.encode(
            {
                'uid': delete_user.uid,
                'nickname': delete_user.nickname,
                'steamId': delete_user.steamId,
                'permissions': [],
                'iat': int(time.time()),
                'exp': int(time.time()) + settings.JWT_EXPIRES_IN
            },
            settings.JWT_SECRET,
            algorithm='HS256'
        )
        
        response = self.client.post(
            '/api/v1/auth/account/delete',
            data=json.dumps({'nickname': 'DeleteUser'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {delete_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain success indicator
        data = response.json()
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(uid=delete_user.uid).exists())
    
    def test_delete_account_with_incorrect_nickname(self):
        """Test POST /api/v1/auth/account/delete - Should return 409 with incorrect nickname"""
        response = self.client.post(
            '/api/v1/auth/account/delete',
            data=json.dumps({'nickname': 'WrongNickname'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 409 Conflict
        self.assertEqual(response.status_code, 409)
        
        # User should still exist
        self.assertTrue(User.objects.filter(uid=self.test_user.uid).exists())
    
    def test_delete_account_unauthenticated(self):
        """Test POST /api/v1/auth/account/delete without token - Should return 401"""
        response = self.client.post(
            '/api/v1/auth/account/delete',
            data=json.dumps({'nickname': 'TestUser'}),
            content_type='application/json'
        )
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)

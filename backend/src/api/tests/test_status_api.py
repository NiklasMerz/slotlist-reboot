"""
API Compatibility Tests for Status Endpoint

Tests that verify the Django Ninja API behaves exactly like the legacy TypeScript/Hapi.js API
for status endpoint.
"""

from django.test import TestCase, Client


class StatusAPICompatibilityTests(TestCase):
    """Test status endpoint for compatibility with legacy API"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_get_status(self):
        """Test GET /api/v1/status - Returns API status"""
        response = self.client.get('/api/v1/status')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain status information
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')
        
        # Should contain uptime information
        self.assertIn('uptime', data)
        self.assertIsInstance(data['uptime'], (int, float))
        self.assertGreaterEqual(data['uptime'], 0)

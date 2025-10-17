# Steam OAuth Authentication Guide

This guide explains how to implement Steam OAuth authentication with the Django backend using Django Ninja.

## Overview

The backend provides Steam OpenID authentication that allows users to sign in using their Steam accounts. The authentication flow is compatible with the original TypeScript implementation.

## Authentication Flow

```
1. Frontend requests Steam login URL from backend
2. Backend generates and returns Steam OpenID URL
3. Frontend redirects user to Steam
4. User authenticates with Steam
5. Steam redirects user back to frontend with OpenID parameters
6. Frontend sends the callback URL to backend for verification
7. Backend verifies with Steam, creates/retrieves user, and returns JWT token
8. Frontend stores JWT and uses it for authenticated requests
```

## API Endpoints

### 1. Get Steam Login URL

**Endpoint:** `GET /api/v1/auth/steam`  
**Authentication:** None required

Retrieves the Steam OpenID URL to redirect the user to for authentication.

**Query Parameters:**
- `return_url` (optional): URL where Steam should redirect after authentication

**Example Request:**
```bash
curl -X GET "https://api.slotlist.info/api/v1/auth/steam?return_url=https://slotlist.info/auth/callback"
```

**Example Response:**
```json
{
  "url": "https://steamcommunity.com/openid/login?openid.ns=http://specs.openid.net/auth/2.0&openid.mode=checkid_setup&..."
}
```

**Frontend Implementation:**
```javascript
// Get Steam login URL
const response = await fetch('/api/v1/auth/steam?return_url=' + encodeURIComponent(window.location.origin + '/auth/callback'));
const data = await response.json();

// Redirect user to Steam
window.location.href = data.url;
```

---

### 2. Verify Steam Login

**Endpoint:** `POST /api/v1/auth/steam`  
**Authentication:** None required

Verifies the Steam OpenID response and returns a JWT token.

**Request Body:**
```json
{
  "url": "https://slotlist.info/auth/callback?openid.ns=http://specs.openid.net/auth/2.0&openid.mode=id_res&..."
}
```

**Example Request:**
```bash
curl -X POST "https://api.slotlist.info/api/v1/auth/steam" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://slotlist.info/auth/callback?openid.ns=..."}'
```

**Example Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "uid": "123e4567-e89b-12d3-a456-426614174000",
    "nickname": "PlayerName",
    "steam_id": "76561198012345678",
    "community": null,
    "active": true
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid Steam OpenID response
- `403 Forbidden`: User account is deactivated

**Frontend Implementation:**
```javascript
// After Steam redirects back to your callback page
const callbackUrl = window.location.href; // Full URL with OpenID parameters

const response = await fetch('/api/v1/auth/steam', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ url: callbackUrl })
});

const data = await response.json();

if (response.ok) {
  // Store the JWT token
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('user', JSON.stringify(data.user));
  
  // Redirect to main app
  window.location.href = '/';
} else {
  console.error('Authentication failed:', data.detail);
}
```

---

### 3. Refresh JWT Token

**Endpoint:** `POST /api/v1/auth/refresh`  
**Authentication:** Required (JWT Bearer token)

Refreshes the JWT token with updated user information and permissions.

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Example Request:**
```bash
curl -X POST "https://api.slotlist.info/api/v1/auth/refresh" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Example Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "uid": "123e4567-e89b-12d3-a456-426614174000",
    "nickname": "UpdatedPlayerName",
    "steam_id": "76561198012345678",
    "community": null,
    "active": true
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User account is deactivated

---

## Configuration

### Environment Variables

Add the following to your `.env` file:

```env
# Steam API Configuration
CONFIG_STEAM_API_SECRET=your-steam-api-key-here

# JWT Configuration (used for OpenID realm)
CONFIG_JWT_ISSUER=https://slotlist.info
CONFIG_JWT_AUDIENCE=https://slotlist.info
```

### Getting a Steam API Key

1. Visit [Steam Web API Key](https://steamcommunity.com/dev/apikey)
2. Sign in with your Steam account
3. Register your domain name
4. Copy the API key to `CONFIG_STEAM_API_SECRET`

---

## Complete Frontend Example

### React/Vue/Angular Example

```javascript
// 1. Initiate Steam login
async function loginWithSteam() {
  const returnUrl = window.location.origin + '/auth/callback';
  
  const response = await fetch(`/api/v1/auth/steam?return_url=${encodeURIComponent(returnUrl)}`);
  const data = await response.json();
  
  // Redirect to Steam
  window.location.href = data.url;
}

// 2. Handle Steam callback (on /auth/callback page)
async function handleSteamCallback() {
  const callbackUrl = window.location.href;
  
  const response = await fetch('/api/v1/auth/steam', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url: callbackUrl })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store token
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    // Redirect to app
    window.location.href = '/';
  } else {
    alert('Login failed: ' + data.detail);
  }
}

// 3. Use token for authenticated requests
async function makeAuthenticatedRequest(url, options = {}) {
  const token = localStorage.getItem('auth_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  return response;
}

// 4. Refresh token periodically
async function refreshToken() {
  const token = localStorage.getItem('auth_token');
  
  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }
}

// Refresh token every 23 hours
setInterval(refreshToken, 23 * 60 * 60 * 1000);
```

---

## Security Considerations

1. **HTTPS Only**: Always use HTTPS in production for Steam OAuth
2. **Token Storage**: Store JWT tokens securely (httpOnly cookies recommended)
3. **Token Expiration**: Tokens expire after 24 hours by default
4. **CORS**: Configure CORS properly to allow your frontend domain
5. **Rate Limiting**: Implement rate limiting on authentication endpoints

---

## Troubleshooting

### "Invalid Steam OpenID response"
- Ensure the callback URL matches the `return_url` parameter
- Check that Steam redirected with all required OpenID parameters
- Verify your Steam API key is correct

### "User account is deactivated"
- The user's account has been deactivated by an administrator
- Contact support to reactivate the account

### "Invalid or expired token"
- The JWT token has expired (24 hours)
- Request a new token using `/api/v1/auth/refresh`
- If refresh fails, redirect user to log in again

---

## Testing

### Test Steam Login Flow

```python
# Test getting Steam login URL
import requests

response = requests.get('http://localhost:8000/api/v1/auth/steam')
print(response.json())
# Output: {'url': 'https://steamcommunity.com/openid/login?...'}
```

### Test with Django Shell

```python
from api.steam_auth import steam_service

# Get login URL
url = steam_service.get_login_url('http://localhost:8000/callback', 'http://localhost:8000')
print(url)

# Get user info from Steam
steam_info = steam_service.get_steam_user_info('76561198012345678')
print(steam_info)
```

---

## API Documentation

The Steam OAuth endpoints are automatically documented in the Django Ninja interactive documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

Visit these URLs after starting the development server to explore the API interactively.

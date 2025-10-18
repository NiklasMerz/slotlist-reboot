# Cloudflare Workers Deployment Guide

This guide explains how to deploy the Django backend to Cloudflare Workers using django-cf.

## Prerequisites

1. **Wrangler CLI**: Install the Cloudflare Wrangler CLI
   ```bash
   npm install -g wrangler
   ```

2. **Cloudflare Account**: You need a Cloudflare account with Workers enabled

3. **Authentication**: Login to Cloudflare
   ```bash
   wrangler login
   ```

## Project Structure

The project has been configured with the following structure for Cloudflare deployment:

```
backend/
├── src/                    # Cloudflare Workers source
│   ├── worker.py          # Workers entrypoint
│   ├── manage.py          # Django management commands
│   ├── slotlist_backend/  # Django project
│   └── api/               # Django app
├── staticfiles/           # Collected static files
├── vendor.txt            # Python dependencies for Workers
├── wrangler.toml         # Wrangler configuration
└── requirements.txt      # Full dependencies (development)
```

## Deployment Steps

### 1. Install Dependencies to Vendor Directory

```bash
cd backend
pip install -t src/vendor -r vendor.txt
```

### 2. Configure Environment Variables

Edit `wrangler.toml` and update the environment variables:

```toml
[env.production.vars]
DJANGO_SECRET_KEY = "your-production-secret-key"
CONFIG_JWT_SECRET = "your-jwt-secret"
CONFIG_STEAM_API_SECRET = "your-steam-api-key"
DEBUG = "False"
ALLOWED_HOSTS = "your-domain.workers.dev,your-custom-domain.com"
```

### 3. Collect Static Files

```bash
python src/manage.py collectstatic --noinput
```

### 4. Deploy to Cloudflare Workers

```bash
npx wrangler deploy
```

## Database Considerations

**Important**: The current configuration uses PostgreSQL which is not directly compatible with Cloudflare Workers. You have several options:

### Option 1: Use Cloudflare D1 (Recommended)
1. Create a D1 database:
   ```bash
   npx wrangler d1 create slotlist-db
   ```

2. Update `wrangler.toml` with the database ID:
   ```toml
   [[d1_databases]]
   binding = "DB"
   database_name = "slotlist-db"
   database_id = "your-database-id"
   ```

3. Modify Django settings to use D1 when deployed

### Option 2: External Database
Configure an external PostgreSQL service (like Neon, Supabase, or PlanetScale) and update the database connection in your settings.

### Option 3: Hybrid Deployment
Keep the database-heavy operations on a traditional server and use Workers for API endpoints only.

## Environment Configuration

The django-cf package has been added to:
- `requirements.txt` - for development
- `vendor.txt` - for Workers deployment
- `INSTALLED_APPS` in Django settings
- Static files configuration updated

## Deployment Commands Summary

```bash
# One-time setup
pip install -t src/vendor -r vendor.txt

# Before each deployment
python src/manage.py collectstatic --noinput
npx wrangler deploy

# For staging environment
npx wrangler deploy --env staging
```

## Custom Domains

To use a custom domain:

1. Add the domain to your Cloudflare account
2. Configure the Workers route in Cloudflare dashboard
3. Update `ALLOWED_HOSTS` in your environment variables

## Monitoring and Logs

View logs with:
```bash
npx wrangler tail
```

## Troubleshooting

1. **Import Errors**: Ensure all dependencies are in `src/vendor`
2. **Static Files**: Make sure `collectstatic` runs before deployment
3. **Database**: Configure appropriate database backend for Workers environment
4. **Environment Variables**: Verify all required variables are set in `wrangler.toml`

## Next Steps

1. Configure database backend for Cloudflare Workers
2. Test all API endpoints after deployment
3. Set up CI/CD pipeline for automated deployments
4. Configure monitoring and error tracking
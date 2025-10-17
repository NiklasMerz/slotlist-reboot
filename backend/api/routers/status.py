from ninja import Router
from api.schemas import StatusResponseSchema
from datetime import datetime

router = Router()

# Store startup time
startup_time = datetime.utcnow()


@router.get('/status', response=StatusResponseSchema, auth=None)
def get_status(request):
    """Get API status and uptime"""
    current_time = datetime.utcnow()
    uptime = int((current_time - startup_time).total_seconds())
    
    return {
        'status': 'operational',
        'uptime': uptime,
        'version': '2.0.0'
    }

"""Mission import API endpoints"""
from ninja import Router
from api.schemas import (
    MissionImportRequestSchema,
    MissionImportResponseSchema,
    ErrorResponseSchema
)
from api.import_utils import (
    fetch_mission_data,
    import_mission,
    preview_import,
    MissionAlreadyExistsError,
    CreatorNotFoundError,
    APIFetchError,
)
from api.routers.auth import JWTAuth


router = Router(tags=['Mission Import'])
jwt_auth = JWTAuth()


@router.post(
    '/import',
    response={200: MissionImportResponseSchema, 400: ErrorResponseSchema, 500: ErrorResponseSchema},
    auth=jwt_auth,
    summary='Import mission from slotlist.info'
)
def import_mission_endpoint(request, payload: MissionImportRequestSchema):
    """
    Import a mission from the old slotlist.info API.
    
    This endpoint fetches mission data from https://api.slotlist.info and imports it
    into the database. You must specify a creator_uid from your database as the mission
    creator.
    
    Set dry_run=true to preview what would be imported without saving to database.
    
    **Authentication required**: Admin or mission.create permission
    
    **Example request:**
    ```json
    {
        "slug": "bf-mm-20251028",
        "creator_uid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "dry_run": false
    }
    ```
    """
    # Check permissions
    user = request.auth
    # TODO: Add proper permission check once permission system is implemented
    # For now, any authenticated user can import
    
    try:
        # Fetch data from slotlist.info API
        mission_data, slots_data = fetch_mission_data(payload.slug)
        
        # If dry run, return preview
        if payload.dry_run:
            preview_data = preview_import(mission_data, slots_data)
            return 200, {
                'preview': preview_data,
                'success': None,
                'message': None,
                'mission_uid': None,
                'mission_slug': None,
                'mission_title': None,
            }
        
        # Actually import the mission
        mission = import_mission(
            payload.slug,
            str(payload.creator_uid) if payload.creator_uid else None,
            mission_data,
            slots_data
        )
        
        return 200, {
            'preview': None,
            'success': True,
            'message': f'Successfully imported mission: {mission.title}',
            'mission_uid': mission.uid,
            'mission_slug': mission.slug,
            'mission_title': mission.title,
        }
        
    except APIFetchError as e:
        return 400, {'detail': str(e)}
    except MissionAlreadyExistsError as e:
        return 400, {'detail': str(e)}
    except CreatorNotFoundError as e:
        return 400, {'detail': str(e)}
    except Exception as e:
        return 500, {'detail': f'Import failed: {str(e)}'}

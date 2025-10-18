from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from api.models import Notification, User
from api.schemas import NotificationSchema

router = Router()


@router.get('/', response=List[NotificationSchema])
def list_notifications(request, limit: int = 25, offset: int = 0, unread_only: bool = False):
    """List notifications for the authenticated user"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    query = Notification.objects.filter(user=user)
    
    if unread_only:
        query = query.filter(read=False)
    
    notifications = query[offset:offset + limit]
    
    return [
        {
            'uid': notif.uid,
            'notification_type': notif.notification_type,
            'title': notif.title,
            'message': notif.message,
            'additional_data': notif.additional_data,
            'read': notif.read,
            'created_at': notif.created_at
        }
        for notif in notifications
    ]


@router.get('/{notification_uid}', response=NotificationSchema)
def get_notification(request, notification_uid: UUID):
    """Get a single notification"""
    user_uid = request.auth.get('user', {}).get('uid')
    notification = get_object_or_404(Notification, uid=notification_uid, user__uid=user_uid)
    
    return {
        'uid': notification.uid,
        'notification_type': notification.notification_type,
        'title': notification.title,
        'message': notification.message,
        'additional_data': notification.additional_data,
        'read': notification.read,
        'created_at': notification.created_at
    }


@router.patch('/{notification_uid}/read')
def mark_notification_read(request, notification_uid: UUID):
    """Mark a notification as read"""
    user_uid = request.auth.get('user', {}).get('uid')
    notification = get_object_or_404(Notification, uid=notification_uid, user__uid=user_uid)
    
    notification.read = True
    notification.save()
    
    return {'success': True}


@router.delete('/{notification_uid}')
def delete_notification(request, notification_uid: UUID):
    """Delete a notification"""
    user_uid = request.auth.get('user', {}).get('uid')
    notification = get_object_or_404(Notification, uid=notification_uid, user__uid=user_uid)
    
    notification.delete()
    
    return {'success': True}

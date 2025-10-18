from django.contrib import admin
from .models import (
    Community,
    User,
    Permission,
    Mission,
    MissionSlotGroup,
    MissionSlot,
    MissionSlotRegistration,
    MissionSlotTemplate,
    MissionAccess,
    CommunityApplication,
    Notification,
)


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'slug', 'website', 'created_at')
    search_fields = ('name', 'tag', 'slug')
    readonly_fields = ('uid', 'created_at', 'updated_at')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'steam_id', 'community', 'active', 'created_at')
    list_filter = ('active', 'community')
    search_fields = ('nickname', 'steam_id')
    readonly_fields = ('uid', 'created_at', 'updated_at')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission', 'created_at')
    list_filter = ('permission',)
    search_fields = ('user__nickname', 'permission')
    readonly_fields = ('uid', 'created_at', 'updated_at')


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'visibility', 'creator', 'community', 'start_time', 'created_at')
    list_filter = ('visibility', 'community', 'start_time')
    search_fields = ('title', 'slug', 'description')
    readonly_fields = ('uid', 'created_at', 'updated_at')


@admin.register(MissionSlotGroup)
class MissionSlotGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'mission', 'order_number', 'created_at')
    list_filter = ('mission',)
    search_fields = ('title', 'mission__title')
    readonly_fields = ('uid', 'created_at', 'updated_at')
    ordering = ('mission', 'order_number')


@admin.register(MissionSlot)
class MissionSlotAdmin(admin.ModelAdmin):
    list_display = ('title', 'slot_group', 'assignee', 'blocked', 'reserve', 'order_number')
    list_filter = ('blocked', 'reserve', 'auto_assignable', 'restricted_community')
    search_fields = ('title', 'slot_group__title', 'assignee__nickname')
    readonly_fields = ('uid', 'created_at', 'updated_at')
    ordering = ('slot_group__mission', 'slot_group__order_number', 'order_number')


@admin.register(MissionSlotRegistration)
class MissionSlotRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'slot', 'created_at')
    search_fields = ('user__nickname', 'slot__title')
    readonly_fields = ('uid', 'created_at', 'updated_at')


@admin.register(MissionSlotTemplate)
class MissionSlotTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'community', 'created_at')
    list_filter = ('community',)
    search_fields = ('title', 'creator__nickname')
    readonly_fields = ('uid', 'created_at', 'updated_at')


@admin.register(MissionAccess)
class MissionAccessAdmin(admin.ModelAdmin):
    list_display = ('mission', 'user', 'community', 'created_at')
    list_filter = ('mission', 'community')
    search_fields = ('mission__title', 'user__nickname', 'community__name')
    readonly_fields = ('uid', 'created_at', 'updated_at')


@admin.register(CommunityApplication)
class CommunityApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'community', 'status', 'created_at')
    list_filter = ('status', 'community')
    search_fields = ('user__nickname', 'community__name')
    readonly_fields = ('uid', 'created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'read', 'created_at')
    list_filter = ('read', 'notification_type')
    search_fields = ('user__nickname', 'title', 'message')
    readonly_fields = ('uid', 'created_at', 'updated_at')

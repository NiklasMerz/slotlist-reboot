import uuid
from django.db import models


# Note: All models have `managed = False` in their Meta class.
# This means Django will NOT create, modify, or delete these database tables.
# The models are designed to work with the existing database schema from the
# original TypeScript/Sequelize backend. This allows for seamless migration
# and the ability to run both backends against the same database.


class Community(models.Model):
    """Represents a community/organization in the system"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    website = models.URLField(max_length=500, null=True, blank=True)
    logo_url = models.URLField(max_length=500, null=True, blank=True, db_column='logoUrl')
    game_servers = models.JSONField(default=list, db_column='gameServers')
    voice_comms = models.JSONField(default=list, db_column='voiceComms')
    repositories = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'communities'
        verbose_name_plural = 'communities'
        managed = False

    def __str__(self):
        return f"{self.name} [{self.tag}]"


class User(models.Model):
    """Represents a user in the system"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nickname = models.CharField(max_length=255)
    steam_id = models.CharField(max_length=255, unique=True, db_column='steamId')
    community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        db_column='communityUid'
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'users'
        managed = False

    def __str__(self):
        return f"{self.nickname} ({self.steam_id})"


class Permission(models.Model):
    """Represents a user permission"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions', db_column='userUid')
    permission = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'permissions'
        unique_together = [['user', 'permission']]
        managed = False

    def __str__(self):
        return f"{self.user.nickname}: {self.permission}"
    
    @staticmethod
    def is_valid_community_permission(community_slug: str, permission: str) -> bool:
        """
        Check if a permission is valid for a community.
        Prevents granting of invalid permissions via direct API requests.
        
        Valid community permissions:
        - community.{slug}.leader
        - community.{slug}.recruitment
        
        Args:
            community_slug: Slug of the community
            permission: Permission string to validate
        
        Returns:
            bool: Whether the permission is valid
        """
        perm = permission.lower()
        return perm == f'community.{community_slug}.leader' or perm == f'community.{community_slug}.recruitment'
    
    @staticmethod
    def is_valid_mission_permission(mission_slug: str, permission: str) -> bool:
        """
        Check if a permission is valid for a mission.
        Prevents granting of invalid permissions via direct API requests.
        
        Valid mission permissions:
        - mission.{slug}.editor
        - mission.{slug}.slotlist.community
        
        Args:
            mission_slug: Slug of the mission
            permission: Permission string to validate
        
        Returns:
            bool: Whether the permission is valid
        """
        perm = permission.lower()
        return perm == f'mission.{mission_slug}.editor' or perm == f'mission.{mission_slug}.slotlist.community'


class Mission(models.Model):
    """Represents a mission/event in the system"""
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('community', 'Community'),
        ('private', 'Private'),
        ('hidden', 'Hidden'),
    ]

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()  # shortDescription in DB
    short_description = models.TextField(db_column='shortDescription')
    detailed_description = models.TextField(db_column='detailedDescription')
    collapsed_description = models.TextField(null=True, blank=True, db_column='collapsedDescription')
    briefing_time = models.DateTimeField(db_column='briefingTime')
    slotting_time = models.DateTimeField(db_column='slottingTime')
    start_time = models.DateTimeField(db_column='startTime')
    end_time = models.DateTimeField(db_column='endTime')
    visibility = models.CharField(max_length=50, choices=VISIBILITY_CHOICES, default='hidden')
    tech_support = models.TextField(null=True, blank=True, db_column='techSupport')
    rules = models.TextField(null=True, blank=True)
    details_map = models.CharField(max_length=255, null=True, blank=True, db_column='detailsMap')
    details_game_mode = models.CharField(max_length=255, null=True, blank=True, db_column='detailsGameMode')
    required_dlcs = models.JSONField(default=list, db_column='requiredDLCs')
    banner_image_url = models.URLField(max_length=500, null=True, blank=True, db_column='bannerImageUrl')
    game_server = models.JSONField(null=True, blank=True, db_column='gameServer')
    voice_comms = models.JSONField(null=True, blank=True, db_column='voiceComms')
    repositories = models.JSONField(default=list)
    mission_token = models.UUIDField(null=True, blank=True, db_column='missionToken')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='missions', db_column='creatorUid')
    community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missions',
        db_column='communityUid'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'missions'
        managed = False

    def __str__(self):
        return self.title


class MissionSlotGroup(models.Model):
    """Represents a slot group within a mission"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    order_number = models.IntegerField(default=0, db_column='orderNumber')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='slot_groups', db_column='missionUid')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'missionSlotGroups'
        ordering = ['order_number', 'title']
        managed = False

    def __str__(self):
        return f"{self.mission.title}: {self.title}"


class MissionSlot(models.Model):
    """Represents a slot within a mission slot group"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    detailed_description = models.TextField(null=True, blank=True, db_column='detailedDescription')
    order_number = models.IntegerField(default=0, db_column='orderNumber')
    required_dlcs = models.JSONField(default=list, db_column='requiredDLCs')
    external_assignee = models.CharField(max_length=255, null=True, blank=True, db_column='externalAssignee')
    slot_group = models.ForeignKey(MissionSlotGroup, on_delete=models.CASCADE, related_name='slots', db_column='slotGroupUid')
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_slots',
        db_column='assigneeUid'
    )
    restricted_community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restricted_slots',
        db_column='restrictedCommunityUid'
    )
    blocked = models.BooleanField(default=False)
    reserve = models.BooleanField(default=False)
    auto_assignable = models.BooleanField(default=True, db_column='autoAssignable')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'missionSlots'
        ordering = ['order_number', 'title']
        managed = False

    def __str__(self):
        return f"{self.slot_group.title}: {self.title}"


class MissionSlotRegistration(models.Model):
    """Represents a user's registration for a mission slot"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slot_registrations', db_column='userUid')
    slot = models.ForeignKey(MissionSlot, on_delete=models.CASCADE, related_name='registrations', db_column='slotUid')
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'missionSlotRegistrations'
        unique_together = [['user', 'slot']]
        managed = False

    def __str__(self):
        return f"{self.user.nickname} -> {self.slot.title}"


class MissionSlotTemplate(models.Model):
    """Represents a reusable slot template"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slot_templates', db_column='creatorUid')
    community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='slot_templates',
        db_column='communityUid'
    )
    slot_groups = models.JSONField(default=list, db_column='slotGroups')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'missionSlotTemplates'
        managed = False

    def __str__(self):
        return self.title


class MissionAccess(models.Model):
    """Represents access rights to a mission"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='accesses', db_column='missionUid')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='mission_accesses',
        db_column='userUid'
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='mission_accesses',
        db_column='communityUid'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'missionAccesses'
        managed = False

    def __str__(self):
        target = self.user.nickname if self.user else self.community.name if self.community else 'Unknown'
        return f"{self.mission.title} -> {target}"


class CommunityApplication(models.Model):
    """Represents a user's application to join a community"""
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', db_column='userUid')
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='applications', db_column='communityUid')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='submitted')
    application_text = models.TextField(db_column='applicationText')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'communityApplications'
        unique_together = [['user', 'community']]
        managed = False

    def __str__(self):
        return f"{self.user.nickname} -> {self.community.name} ({self.status})"


class Notification(models.Model):
    """Represents a notification for a user"""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', db_column='userUid')
    notification_type = models.CharField(max_length=255, db_column='notificationType')
    title = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    additional_data = models.JSONField(null=True, blank=True, db_column='additionalData')
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        managed = False

    def __str__(self):
        return f"{self.user.nickname}: {self.notification_type}"


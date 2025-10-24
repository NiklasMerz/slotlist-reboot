from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from ninja import Schema, Field


class CommunitySchema(Schema):
    uid: UUID
    name: str
    tag: str
    slug: str
    website: Optional[str] = None
    image_url: Optional[str] = None
    game_servers: Optional[List[Any]] = None
    voice_comms: Optional[List[Any]] = None
    repositories: Optional[List[Any]] = None


class UserSchema(Schema):
    uid: UUID
    nickname: str
    steam_id: Optional[str] = None
    community: Optional[CommunitySchema] = None
    active: Optional[bool] = None


class UserDetailSchema(UserSchema):
    missions: Optional[List['MissionSchema']] = []


class PermissionSchema(Schema):
    uid: UUID
    permission: str


class MissionSlotGroupSchema(Schema):
    uid: UUID
    title: str
    description: str
    order_number: int


class MissionSlotSchema(Schema):
    uid: UUID
    title: str
    description: str
    detailed_description: str
    order_number: int
    required_dlcs: Optional[List[str]] = None
    assignee: Optional[UserSchema] = None
    restricted_community: Optional[CommunitySchema] = None
    blocked: bool
    reserve: bool
    auto_assignable: bool


class MissionSlotRegistrationSchema(Schema):
    uid: UUID
    user: UserSchema
    slot: MissionSlotSchema
    comment: str


class MissionSchema(Schema):
    uid: UUID
    slug: str
    title: str
    description: str
    briefing_time: Optional[datetime] = None
    slot_list_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    visibility: str
    tech_teleport: bool
    tech_respawn: bool
    details_map: Optional[str] = None
    details_game_mode: Optional[str] = None
    details_required_dlcs: Optional[List[str]] = None
    game_server: Optional[Any] = None
    voice_comms: Optional[Any] = None
    repositories: Optional[List[Any]] = None
    rules_of_engagement: str
    image_url: Optional[str] = None
    creator: UserSchema
    community: Optional[CommunitySchema] = None


class MissionSlotTemplateSchema(Schema):
    uid: UUID
    title: str
    creator: UserSchema
    community: Optional[CommunitySchema] = None
    slot_groups: List[Any]


class MissionAccessSchema(Schema):
    uid: UUID
    mission: MissionSchema
    user: Optional[UserSchema] = None
    community: Optional[CommunitySchema] = None


class CommunityApplicationSchema(Schema):
    uid: UUID
    user: UserSchema
    community: CommunitySchema
    status: str
    application_text: str


class NotificationSchema(Schema):
    uid: UUID
    notification_type: str
    title: Optional[str] = None
    message: str
    additional_data: Optional[Any] = None
    read: bool
    created_at: datetime


# Input Schemas for creating/updating
class MissionCreateSchema(Schema):
    title: str
    slug: Optional[str] = None
    description: Optional[str] = ''
    briefing_time: Optional[datetime] = Field(None, alias='briefingTime')
    slotting_time: Optional[datetime] = Field(None, alias='slottingTime')
    start_time: Optional[datetime] = Field(None, alias='startTime')
    end_time: Optional[datetime] = Field(None, alias='endTime')
    visibility: str = 'hidden'
    tech_teleport: bool = Field(False, alias='techTeleport')
    tech_respawn: bool = Field(False, alias='techRespawn')
    details_map: Optional[str] = Field(None, alias='detailsMap')
    details_game_mode: Optional[str] = Field(None, alias='detailsGameMode')
    required_dlcs: Optional[List[str]] = Field(None, alias='requiredDLCs')
    game_server: Optional[Any] = Field(None, alias='gameServer')
    voice_comms: Optional[Any] = Field(None, alias='voiceComms')
    repositories: Optional[List[Any]] = None
    rules_of_engagement: Optional[str] = Field('', alias='rulesOfEngagement')
    community_uid: Optional[UUID] = None
    
    class Config:
        populate_by_name = True


class MissionUpdateSchema(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    briefing_time: Optional[datetime] = Field(None, alias='briefingTime')
    slotting_time: Optional[datetime] = Field(None, alias='slottingTime')
    start_time: Optional[datetime] = Field(None, alias='startTime')
    end_time: Optional[datetime] = Field(None, alias='endTime')
    visibility: Optional[str] = None
    tech_teleport: Optional[bool] = Field(None, alias='techTeleport')
    tech_respawn: Optional[bool] = Field(None, alias='techRespawn')
    details_map: Optional[str] = Field(None, alias='detailsMap')
    details_game_mode: Optional[str] = Field(None, alias='detailsGameMode')
    required_dlcs: Optional[List[str]] = Field(None, alias='requiredDLCs')
    game_server: Optional[Any] = Field(None, alias='gameServer')
    voice_comms: Optional[Any] = Field(None, alias='voiceComms')
    repositories: Optional[List[Any]] = None
    rules_of_engagement: Optional[str] = Field(None, alias='rulesOfEngagement')
    
    class Config:
        populate_by_name = True


class UserUpdateSchema(Schema):
    nickname: Optional[str] = None


class CommunityCreateSchema(Schema):
    name: str
    tag: str
    website: Optional[str] = None
    game_servers: Optional[List[Any]] = None
    voice_comms: Optional[List[Any]] = None
    repositories: Optional[List[Any]] = None


class CommunityUpdateSchema(Schema):
    name: Optional[str] = None
    tag: Optional[str] = None
    website: Optional[str] = None
    game_servers: Optional[List[Any]] = None
    voice_comms: Optional[List[Any]] = None
    repositories: Optional[List[Any]] = None


class AuthResponseSchema(Schema):
    token: str
    user: UserSchema


class ErrorResponseSchema(Schema):
    detail: str


class StatusResponseSchema(Schema):
    status: str
    uptime: Optional[int] = None
    version: str

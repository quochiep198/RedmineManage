from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class RedmineConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    base_url: AnyHttpUrl
    identifier: str = Field(min_length=1, max_length=255)
    api_key: str = Field(min_length=1)


class RedmineConnectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    base_url: AnyHttpUrl | None = None
    identifier: str | None = Field(default=None, min_length=1, max_length=255)
    api_key: str | None = Field(default=None, min_length=1)


class RedmineConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str
    identifier: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_tested_at: datetime | None


class RedmineConnectionTestResponse(BaseModel):
    success: bool
    message: str
    status: str
    redmine_user: dict[str, object]
    last_tested_at: datetime

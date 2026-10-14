"""API models and input bounds."""
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class Profile(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    device: str = Field(min_length=1, max_length=90)
    group_name: str = Field(default="", max_length=60)
    tags: list[str] = Field(default_factory=list, max_length=20)
    locale: str = Field(default="pt-BR", pattern=r"^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$")
    timezone: str = Field(default="America/Sao_Paulo", min_length=1, max_length=80)
    viewport_width: int | None = Field(default=None, ge=240, le=3840)
    viewport_height: int | None = Field(default=None, ge=320, le=3840)
    proxy_id: str | None = None

    @field_validator("name")
    @classmethod
    def trim(cls, value):
        if not value.strip():
            raise ValueError("Empty name")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def check_tags(cls, tags):
        if any(not t.strip() or len(t) > 30 for t in tags):
            raise ValueError("Tags must have 1..30 characters")
        return tags


class Proxy(BaseModel):
    name: str = Field(default="Proxy", min_length=1, max_length=80)
    scheme: Literal["http", "https", "socks5"] = "http"
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(ge=1, le=65535)
    username: str | None = Field(default=None, max_length=150)
    password: str | None = Field(default=None, max_length=500)


class ProxyImport(BaseModel):
    lines: str = Field(min_length=1, max_length=200000)


class Settings(BaseModel):
    max_active: int = Field(ge=1, le=20)
    warn_duplicate_proxy: bool

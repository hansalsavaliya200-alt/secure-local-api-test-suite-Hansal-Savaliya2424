"""Request schemas. Allow-list validation: unknown fields, wrong types and bad sizes are rejected."""
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Priority = Literal["low", "normal", "high"]
TicketStatus = Literal["open", "in_progress", "resolved", "closed"]
Role = Literal["user", "agent", "admin"]


def reject_control_chars(value: str, allow_whitespace_controls: bool = False) -> str:
    for ch in value:
        if unicodedata.category(ch) == "Cc" and not (allow_whitespace_controls and ch in "\n\r\t"):
            raise ValueError("control characters are not allowed")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")  # MUT:forbid-extra


class LoginRequest(StrictModel):
    username: str = Field(min_length=1, max_length=32, pattern=r"^[a-z0-9_]+$")
    password: str = Field(min_length=1, max_length=128)  # not stripped: spaces may be part of a password


class TextModel(StrictModel):
    model_config = ConfigDict(str_strip_whitespace=True)  # extra="forbid" is inherited from StrictModel


class TicketCreate(TextModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    priority: Priority = "normal"

    @field_validator("title")
    @classmethod
    def _title_clean(cls, v):
        return reject_control_chars(v)

    @field_validator("description")
    @classmethod
    def _description_clean(cls, v):
        return reject_control_chars(v, allow_whitespace_controls=True)


class StatusUpdate(TextModel):
    status: TicketStatus


class RoleUpdate(TextModel):
    role: Role

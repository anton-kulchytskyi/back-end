from enum import Enum


class Role(str, Enum):
    """User roles in a company."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

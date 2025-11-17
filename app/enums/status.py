from enum import Enum


class Status(str, Enum):
    """Status of company invitation and membership request."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

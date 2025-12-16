from enum import Enum


class NotificationStatus(str, Enum):
    """Lifecycle status of a user notification."""

    UNREAD = "unread"
    READ = "read"
    # future:
    # DISMISSED = "dismissed"
    # ARCHIVED = "archived"

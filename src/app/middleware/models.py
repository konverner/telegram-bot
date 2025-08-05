from datetime import datetime


class Event:
    """Event model"""
    def __init__(self, user_id, content, content_type, event_type, state=None):
        self.user_id = user_id
        self.content = content
        self.content_type = content_type
        self.event_type = event_type
        self.state = state
        self.created_at = datetime.now()

    def dict(self) -> dict:
        """Return a dictionary representation of the event"""
        return {
            "timestamp": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "user_id": self.user_id,
            "event_type": self.event_type,
            "state": self.state,
            "content": self.content,
            "content_type": self.content_type,
        }

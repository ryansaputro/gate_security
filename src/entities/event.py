from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class EventAttendee:
    family_id: str = ""
    name: str = ""
    status: str = "pending"  # confirmed | declined | pending
    attended: bool = False


@dataclass
class Event:
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    type: str = ""  # meeting | social | maintenance | emergency | announcement
    location: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    organizer: str = ""
    target_audience: str = "all"  # all | block_a | block_b | ...
    is_mandatory: bool = False
    rsvp_required: bool = False
    attendees: List[EventAttendee] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    status: str = "upcoming"  # upcoming | ongoing | completed | cancelled
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

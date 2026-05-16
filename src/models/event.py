from entities.event import Event, EventAttendee

COLLECTION_NAME = "events"


def _attendee_to_document(attendee: EventAttendee) -> dict:
    return {
        "familyId": attendee.family_id,
        "name": attendee.name,
        "status": attendee.status,
        "attended": attendee.attended,
    }


def _attendee_from_document(doc: dict) -> EventAttendee:
    return EventAttendee(
        family_id=doc.get("familyId", ""),
        name=doc.get("name", ""),
        status=doc.get("status", "pending"),
        attended=doc.get("attended", False),
    )


def to_document(entity: Event) -> dict:
    doc = {
        "title": entity.title,
        "description": entity.description,
        "type": entity.type,
        "location": entity.location,
        "startDate": entity.start_date,
        "endDate": entity.end_date,
        "organizer": entity.organizer,
        "targetAudience": entity.target_audience,
        "isMandatory": entity.is_mandatory,
        "rsvpRequired": entity.rsvp_required,
        "attendees": [_attendee_to_document(a) for a in entity.attendees],
        "attachments": entity.attachments,
        "status": entity.status,
        "createdBy": entity.created_by,
        "createdAt": entity.created_at,
        "updatedAt": entity.updated_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> Event:
    return Event(
        id=str(doc.get("_id", "")),
        title=doc.get("title", ""),
        description=doc.get("description", ""),
        type=doc.get("type", ""),
        location=doc.get("location", ""),
        start_date=doc.get("startDate"),
        end_date=doc.get("endDate"),
        organizer=doc.get("organizer", ""),
        target_audience=doc.get("targetAudience", "all"),
        is_mandatory=doc.get("isMandatory", False),
        rsvp_required=doc.get("rsvpRequired", False),
        attendees=[_attendee_from_document(a) for a in doc.get("attendees", [])],
        attachments=doc.get("attachments", []),
        status=doc.get("status", "upcoming"),
        created_by=doc.get("createdBy", ""),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )

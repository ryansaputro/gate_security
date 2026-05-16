"""
MongoDB collection models.
Each model maps entity <-> MongoDB document and handles indexes.
"""

from models import (
    access_log,
    due,
    event,
    family,
    guest,
    house,
    master_data,
    rfid_card,
    setting,
    vehicle,
)

COLLECTIONS = {
    "houses": house.COLLECTION_NAME,
    "families": family.COLLECTION_NAME,
    "vehicles": vehicle.COLLECTION_NAME,
    "guests": guest.COLLECTION_NAME,
    "dues": due.COLLECTION_NAME,
    "rfid_cards": rfid_card.COLLECTION_NAME,
    "settings": setting.COLLECTION_NAME,
    "master_data": master_data.COLLECTION_NAME,
    "events": event.COLLECTION_NAME,
    "access_logs": access_log.COLLECTION_NAME,
}


def create_indexes(db):
    """Create all collection indexes."""
    # vehicles - fast plate lookup
    db.vehicles.create_index("plateNumberNormalized")
    db.vehicles.create_index([("familyId", 1), ("isActive", 1)])

    # rfid_cards - fast card scan
    db.rfid_cards.create_index("cardUid", unique=True)
    db.rfid_cards.create_index([("familyId", 1), ("isActive", 1)])

    # dues - check unpaid per family
    db.dues.create_index([("familyId", 1), ("status", 1), ("period", -1)])
    db.dues.create_index([("houseId", 1), ("period", -1)])

    # access_logs - recent history
    db.access_logs.create_index([("timestamp", -1)])
    db.access_logs.create_index([("plateDetected", 1), ("timestamp", -1)])
    db.access_logs.create_index([("rfidCardId", 1), ("timestamp", -1)])

    # guests - active guests
    db.guests.create_index([("status", 1), ("entryTime", -1)])
    db.guests.create_index("vehiclePlate")

    # houses
    db.houses.create_index([("block", 1), ("houseNumber", 1)], unique=True)

    # families
    db.families.create_index("houseId")

    # settings
    db.settings.create_index("key", unique=True)

    # master_data
    db.master_data.create_index([("type", 1), ("code", 1)], unique=True)

    # events
    db.events.create_index([("status", 1), ("startDate", -1)])

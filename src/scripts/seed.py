"""
Database Seeder - Populate all collections with sample data.
Run: make seed
  or: python3 src/scripts/seed.py
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from drivers.mongo.connection import Mongo
from models import create_indexes

mongo = Mongo()
db = mongo.get_db()


def drop_all():
    """Drop all collections for clean seed."""
    collections = ["houses", "families", "vehicles", "guests", "rfid_cards",
                   "access_logs", "dues", "events", "settings", "master_data"]
    for col in collections:
        db[col].drop()
    print("  Dropped all collections")


def seed_houses():
    """Seed 10 houses across 2 blocks."""
    houses = []
    for block in ["A", "B"]:
        for num in range(1, 6):
            houses.append({
                "block": block,
                "street": f"Jalan {'Melati' if block == 'A' else 'Mawar'}",
                "houseNumber": str(num),
                "headOfFamilyId": None,
                "status": "occupied",
                "latitude": -6.2088 + (num * 0.001),
                "longitude": 106.8456 + (num * 0.001),
                "addressNote": f"Blok {block} No.{num}",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            })
    db.houses.insert_many(houses)
    print(f"  Seeded {len(houses)} houses")
    return list(db.houses.find())


def seed_families(houses):
    """Seed families linked to houses."""
    names = [
        ("Budi Santoso", "+6281234567001"),
        ("Agus Wijaya", "+6281234567002"),
        ("Siti Rahayu", "+6281234567003"),
        ("Dedi Kurniawan", "+6281234567004"),
        ("Rina Marlina", "+6281234567005"),
        ("Hendra Gunawan", "+6281234567006"),
        ("Dewi Lestari", "+6281234567007"),
        ("Eko Prasetyo", "+6281234567008"),
        ("Fitri Handayani", "+6281234567009"),
        ("Joko Susilo", "+6281234567010"),
    ]
    families = []
    for i, house in enumerate(houses):
        name, phone = names[i]
        families.append({
            "houseId": str(house["_id"]),
            "headName": name,
            "headPhone": phone,
            "headIdNumber": f"320100000000{i+1:04d}",
            "members": [
                {"name": f"Istri {name.split()[0]}", "relation": "wife", "phone": "", "idNumber": "", "isActive": True},
                {"name": f"Anak {name.split()[0]}", "relation": "child", "phone": "", "idNumber": "", "isActive": True},
            ],
            "totalMembers": 3,
            "moveInDate": datetime(2020, 1, 1) + timedelta(days=i * 30),
            "status": "active",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        })
    db.families.insert_many(families)
    print(f"  Seeded {len(families)} families")
    # Update house headOfFamilyId
    all_families = list(db.families.find())
    for fam in all_families:
        db.houses.update_one({"_id": db.houses.find_one({"_id": {"$in": [h["_id"] for h in houses]}})["_id"]}, {"$set": {"headOfFamilyId": str(fam["_id"])}})
    return all_families


def seed_vehicles(families):
    """Seed vehicles for each family."""
    plates = [
        ("B 1234 ABC", "car", "Toyota", "Avanza", "Silver", 2020),
        ("B 5678 DEF", "car", "Honda", "Jazz", "White", 2019),
        ("D 9012 GHI", "motorcycle", "Honda", "Vario", "Black", 2021),
        ("B 3456 JKL", "car", "Daihatsu", "Xenia", "Grey", 2018),
        ("F 7890 MNO", "motorcycle", "Yamaha", "NMAX", "Blue", 2022),
        ("B 2345 PQR", "car", "Mitsubishi", "Xpander", "Red", 2021),
        ("B 6789 STU", "car", "Suzuki", "Ertiga", "White", 2020),
        ("AB 1234 VW", "motorcycle", "Honda", "Beat", "Red", 2023),
        ("B 4567 XYZ", "car", "Toyota", "Innova", "Black", 2019),
        ("D 8901 ABC", "car", "Nissan", "Livina", "Silver", 2020),
    ]
    vehicles = []
    for i, fam in enumerate(families):
        plate, vtype, brand, model, color, year = plates[i]
        vehicles.append({
            "familyId": str(fam["_id"]),
            "plateNumber": plate,
            "plateNumberNormalized": plate.replace(" ", "").upper(),
            "type": vtype,
            "brand": brand,
            "model": model,
            "color": color,
            "year": year,
            "stnkExpiry": datetime(2027, 3, 15),
            "photoUrl": "",
            "isActive": True,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        })
    db.vehicles.insert_many(vehicles)
    print(f"  Seeded {len(vehicles)} vehicles")
    return list(db.vehicles.find())


def seed_rfid_cards(families, vehicles):
    """Seed RFID cards for families."""
    uids = ["A1B2C3D4", "E5F6G7H8", "I9J0K1L2", "M3N4O5P6", "Q7R8S9T0",
            "U1V2W3X4", "Y5Z6A7B8", "C9D0E1F2", "G3H4I5J6", "K7L8M9N0"]
    cards = []
    for i, fam in enumerate(families):
        cards.append({
            "cardUid": uids[i],
            "familyId": str(fam["_id"]),
            "holderName": fam["headName"],
            "vehicleIds": [str(vehicles[i]["_id"])] if i < len(vehicles) else [],
            "cardType": "resident",
            "isActive": True,
            "blockedReason": "",
            "issuedAt": datetime.now() - timedelta(days=365),
            "expiresAt": datetime.now() + timedelta(days=365),
            "lastUsedAt": datetime.now() - timedelta(hours=i),
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        })
    db.rfid_cards.insert_many(cards)
    print(f"  Seeded {len(cards)} RFID cards")


def seed_dues(families, houses):
    """Seed dues (iuran) - some paid, some unpaid."""
    dues = []
    for i, fam in enumerate(families):
        house = houses[i] if i < len(houses) else houses[0]
        for month in range(1, 7):  # Jan-Jun 2026
            status = "paid" if month <= 4 else ("unpaid" if i % 3 != 0 else "overdue")
            dues.append({
                "familyId": str(fam["_id"]),
                "houseId": str(house["_id"]),
                "period": f"2026-{month:02d}",
                "year": 2026,
                "month": month,
                "type": "monthly",
                "amount": 150000,
                "paidAmount": 150000 if status == "paid" else 0,
                "status": status,
                "paidAt": datetime(2026, month, 10) if status == "paid" else None,
                "paymentMethod": "transfer" if status == "paid" else "",
                "receiptNumber": f"RCP-2026{month:02d}-{i+1:03d}" if status == "paid" else "",
                "collectorName": "Pak RT" if status == "paid" else "",
                "dueDate": datetime(2026, month, 5),
                "notes": "",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            })
    db.dues.insert_many(dues)
    print(f"  Seeded {len(dues)} dues records")


def seed_guests(houses):
    """Seed some active guests."""
    guests = [
        {"name": "Ahmad Delivery", "purpose": "delivery", "plate": "B 9999 GOJ", "vtype": "motorcycle"},
        {"name": "Tukang Ledeng", "purpose": "service", "plate": "", "vtype": "none"},
        {"name": "Pak Pos", "purpose": "delivery", "plate": "B 7777 POS", "vtype": "motorcycle"},
        {"name": "Tamu Budi", "purpose": "visit", "plate": "D 1111 XYZ", "vtype": "car"},
    ]
    docs = []
    for i, g in enumerate(guests):
        docs.append({
            "visitingHouseId": str(houses[i % len(houses)]["_id"]),
            "visitingFamilyId": "",
            "guestName": g["name"],
            "guestPhone": f"+628123456{80+i:02d}",
            "guestIdNumber": "",
            "purpose": g["purpose"],
            "vehiclePlate": g["plate"],
            "vehicleType": g["vtype"],
            "entryTime": datetime.now() - timedelta(hours=i),
            "exitTime": None,
            "entryGate": "gate_1",
            "exitGate": "",
            "entryPhotoUrl": "",
            "approvedBy": "security",
            "status": "inside",
            "notes": "",
            "createdAt": datetime.now(),
        })
    db.guests.insert_many(docs)
    print(f"  Seeded {len(docs)} guests")


def seed_access_logs(families, vehicles):
    """Seed recent access logs."""
    logs = []
    for i in range(20):
        fam = families[i % len(families)]
        veh = vehicles[i % len(vehicles)]
        method = "rfid" if i % 2 == 0 else "plate_ocr"
        logs.append({
            "gateId": f"gate_{1 + i % 2}",
            "direction": "entry" if i % 3 != 0 else "exit",
            "method": method,
            "rfidCardId": None,
            "vehicleId": str(veh["_id"]) if method == "plate_ocr" else None,
            "plateDetected": veh["plateNumberNormalized"] if method == "plate_ocr" else "",
            "plateConfidence": 0.92 if method == "plate_ocr" else 0.0,
            "familyId": str(fam["_id"]),
            "isResident": True,
            "validationResult": "granted",
            "deniedReason": "",
            "photoUrl": "",
            "timestamp": datetime.now() - timedelta(minutes=i * 30),
        })
    db.access_logs.insert_many(logs)
    print(f"  Seeded {len(logs)} access logs")


def seed_events():
    """Seed community events."""
    events = [
        {
            "title": "Rapat RT Bulanan",
            "description": "Agenda: iuran, keamanan, kebersihan",
            "type": "meeting",
            "location": "Balai Warga",
            "startDate": datetime(2026, 6, 1, 19, 0),
            "endDate": datetime(2026, 6, 1, 21, 0),
            "organizer": "Pak RT",
            "targetAudience": "all",
            "isMandatory": True,
            "rsvpRequired": False,
            "attendees": [],
            "attachments": [],
            "status": "upcoming",
            "createdBy": "admin",
        },
        {
            "title": "Kerja Bakti",
            "description": "Bersih-bersih lingkungan",
            "type": "maintenance",
            "location": "Area Taman",
            "startDate": datetime(2026, 6, 8, 7, 0),
            "endDate": datetime(2026, 6, 8, 11, 0),
            "organizer": "Pak RW",
            "targetAudience": "all",
            "isMandatory": False,
            "rsvpRequired": False,
            "attendees": [],
            "attachments": [],
            "status": "upcoming",
            "createdBy": "admin",
        },
        {
            "title": "Lomba 17 Agustus",
            "description": "Lomba balap karung, makan kerupuk, dll",
            "type": "social",
            "location": "Lapangan",
            "startDate": datetime(2026, 8, 17, 8, 0),
            "endDate": datetime(2026, 8, 17, 16, 0),
            "organizer": "Panitia HUT RI",
            "targetAudience": "all",
            "isMandatory": False,
            "rsvpRequired": True,
            "attendees": [],
            "attachments": [],
            "status": "upcoming",
            "createdBy": "admin",
        },
    ]
    for e in events:
        e["createdAt"] = datetime.now()
        e["updatedAt"] = datetime.now()
    db.events.insert_many(events)
    print(f"  Seeded {len(events)} events")


def seed_settings():
    """Seed system settings."""
    settings = [
        {"key": "gate_mode", "value": "rfid_primary", "category": "gate", "description": "Primary gate validation method (rfid_primary|plate_only|rfid_only|both_required)"},
        {"key": "dues_block_enabled", "value": "true", "category": "dues", "description": "Block access for unpaid dues"},
        {"key": "ocr_confidence_threshold", "value": "0.6", "category": "gate", "description": "Minimum OCR confidence for plate fuzzy match (0.0-1.0)"},
        {"key": "ocr_vote_threshold", "value": "3", "category": "gate", "description": "Minimum OCR votes before triggering gate validation"},
        {"key": "gate_cooldown_seconds", "value": "10", "category": "gate", "description": "Cooldown seconds between gate open for same plate"},
        {"key": "guest_max_hours", "value": "12", "category": "gate", "description": "Max hours guest can stay before expired"},
        {"key": "notification_whatsapp", "value": "true", "category": "notification", "description": "Send WA notifications"},
    ]
    for s in settings:
        s["updatedBy"] = "admin"
        s["updatedAt"] = datetime.now()
    db.settings.insert_many(settings)
    print(f"  Seeded {len(settings)} settings")


def seed_master_data():
    """Seed master data."""
    data = [
        # Gates
        {"type": "gate", "code": "gate_1", "name": "Gerbang Utama", "description": "Pintu masuk utama", "metadata": {"direction": "both"}, "sortOrder": 1},
        {"type": "gate", "code": "gate_2", "name": "Gerbang Belakang", "description": "Pintu keluar belakang", "metadata": {"direction": "exit_only"}, "sortOrder": 2},
        # Blocks
        {"type": "block", "code": "A", "name": "Blok A", "description": "Jalan Melati", "metadata": {"totalHouses": 5}, "sortOrder": 1},
        {"type": "block", "code": "B", "name": "Blok B", "description": "Jalan Mawar", "metadata": {"totalHouses": 5}, "sortOrder": 2},
        # Vehicle brands
        {"type": "vehicle_brand", "code": "TOYOTA", "name": "Toyota", "description": "", "metadata": {}, "sortOrder": 1},
        {"type": "vehicle_brand", "code": "HONDA", "name": "Honda", "description": "", "metadata": {}, "sortOrder": 2},
        {"type": "vehicle_brand", "code": "DAIHATSU", "name": "Daihatsu", "description": "", "metadata": {}, "sortOrder": 3},
        {"type": "vehicle_brand", "code": "SUZUKI", "name": "Suzuki", "description": "", "metadata": {}, "sortOrder": 4},
        {"type": "vehicle_brand", "code": "YAMAHA", "name": "Yamaha", "description": "", "metadata": {}, "sortOrder": 5},
        # Due types
        {"type": "due_type", "code": "monthly", "name": "Iuran Bulanan", "description": "Rp 150.000/bulan", "metadata": {"amount": 150000}, "sortOrder": 1},
        {"type": "due_type", "code": "security", "name": "Iuran Keamanan", "description": "Rp 50.000/bulan", "metadata": {"amount": 50000}, "sortOrder": 2},
        {"type": "due_type", "code": "cleaning", "name": "Iuran Kebersihan", "description": "Rp 75.000/bulan", "metadata": {"amount": 75000}, "sortOrder": 3},
    ]
    for d in data:
        d["isActive"] = True
        d["createdAt"] = datetime.now()
        d["updatedAt"] = datetime.now()
    db.master_data.insert_many(data)
    print(f"  Seeded {len(data)} master data entries")


def main():
    print("\n🌱 Seeding database...")
    print(f"   DB: {os.getenv('MONGO_DB', 'gate_security')}")
    print()

    drop_all()

    houses = seed_houses()
    families = seed_families(houses)
    vehicles = seed_vehicles(families)
    seed_rfid_cards(families, vehicles)
    seed_dues(families, houses)
    seed_guests(houses)
    seed_access_logs(families, vehicles)
    seed_events()
    seed_settings()
    seed_master_data()

    print("\n📦 Creating indexes...")
    create_indexes(db)

    print("\n✅ Seed complete!")
    print(f"   Houses: {db.houses.count_documents({})}")
    print(f"   Families: {db.families.count_documents({})}")
    print(f"   Vehicles: {db.vehicles.count_documents({})}")
    print(f"   RFID Cards: {db.rfid_cards.count_documents({})}")
    print(f"   Dues: {db.dues.count_documents({})}")
    print(f"   Guests: {db.guests.count_documents({})}")
    print(f"   Access Logs: {db.access_logs.count_documents({})}")
    print(f"   Events: {db.events.count_documents({})}")
    print(f"   Settings: {db.settings.count_documents({})}")
    print(f"   Master Data: {db.master_data.count_documents({})}")
    print()

    mongo.close()


if __name__ == "__main__":
    main()

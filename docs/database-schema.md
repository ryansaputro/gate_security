# Database Schema - Residential Gate Security System

MongoDB collections for integrated plate detection + RFID gate access.

## Collections

### 1. `houses`

Residential unit/house data.

```json
{
  "_id": "ObjectId",
  "block": "A",
  "street": "Jalan Melati",
  "house_number": "12",
  "head_of_family_id": "ObjectId (ref: families)",
  "status": "occupied | vacant | rented",
  "latitude": -6.2088,
  "longitude": 106.8456,
  "address_note": "Dekat taman",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### 2. `families`

Family (KK) data with members.

```json
{
  "_id": "ObjectId",
  "house_id": "ObjectId (ref: houses)",
  "head_name": "John Doe",
  "head_phone": "+6281234567890",
  "head_id_number": "3201xxxxxxxxxxxx",
  "members": [
    {
      "name": "Jane Doe",
      "relation": "wife | child | parent | sibling | other",
      "phone": "+6281234567891",
      "id_number": "3201xxxxxxxxxxxx",
      "birth_date": "ISODate",
      "is_active": true
    }
  ],
  "total_members": 4,
  "move_in_date": "ISODate",
  "status": "active | moved_out",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### 3. `vehicles`

Registered vehicles owned by residents.

```json
{
  "_id": "ObjectId",
  "family_id": "ObjectId (ref: families)",
  "plate_number": "B 1234 XYZ",
  "plate_number_normalized": "B1234XYZ",
  "type": "car | motorcycle",
  "brand": "Toyota",
  "model": "Avanza",
  "color": "Silver",
  "year": 2020,
  "stnk_expiry": "ISODate",
  "photo_url": "https://...",
  "is_active": true,
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### 4. `guests`

Guest/visitor log.

```json
{
  "_id": "ObjectId",
  "visiting_house_id": "ObjectId (ref: houses)",
  "visiting_family_id": "ObjectId (ref: families)",
  "guest_name": "Ahmad",
  "guest_phone": "+6281234567892",
  "guest_id_number": "3201xxxxxxxxxxxx",
  "purpose": "visit | delivery | service | contractor | other",
  "vehicle_plate": "D 5678 ABC",
  "vehicle_type": "car | motorcycle | none",
  "entry_time": "ISODate",
  "exit_time": "ISODate",
  "entry_gate": "gate_1",
  "exit_gate": "gate_1",
  "entry_photo_url": "https://...",
  "approved_by": "resident | security",
  "status": "inside | exited | expired",
  "notes": "Tukang AC",
  "created_at": "ISODate"
}
```

### 5. `dues` (Iuran)

Monthly resident dues/fees tracking.

```json
{
  "_id": "ObjectId",
  "family_id": "ObjectId (ref: families)",
  "house_id": "ObjectId (ref: houses)",
  "period": "2026-05",
  "year": 2026,
  "month": 5,
  "type": "monthly | security | cleaning | parking | other",
  "amount": 350000,
  "paid_amount": 350000,
  "status": "paid | unpaid | partial | overdue",
  "paid_at": "ISODate",
  "payment_method": "cash | transfer | qris",
  "receipt_number": "INV-202605-001",
  "collector_name": "Pak RT",
  "due_date": "ISODate",
  "notes": "",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### 6. `rfid_cards`

RFID card registration. One card can be linked to multiple vehicles.

```json
{
  "_id": "ObjectId",
  "card_uid": "A1B2C3D4",
  "family_id": "ObjectId (ref: families)",
  "holder_name": "John Doe",
  "vehicle_ids": ["ObjectId", "ObjectId"],
  "card_type": "resident | temporary | master",
  "is_active": true,
  "blocked_reason": "unpaid_dues | lost | expired",
  "issued_at": "ISODate",
  "expires_at": "ISODate",
  "last_used_at": "ISODate",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### 7. `settings`

System configuration.

```json
{
  "_id": "ObjectId",
  "key": "gate_mode",
  "value": "rfid_only | plate_only | rfid_and_plate | open",
  "category": "gate | dues | notification | general",
  "description": "Gate validation mode",
  "updated_by": "admin",
  "updated_at": "ISODate"
}
```

Common settings:
| Key | Values | Description |
|-----|--------|-------------|
| `gate_mode` | rfid_only, plate_only, rfid_and_plate, open | How gate validates entry |
| `dues_block_enabled` | true/false | Block RFID if dues unpaid |
| `dues_grace_period_days` | 30 | Days before blocking |
| `guest_max_duration_hours` | 24 | Auto-expire guest after N hours |
| `plate_detection_confidence` | 0.7 | Min OCR confidence to accept |
| `notification_channel` | whatsapp, telegram, none | Alert channel |

### 8. `master_data`

Reference/master data (facilities, categories, etc).

```json
{
  "_id": "ObjectId",
  "type": "facility | vehicle_brand | gate | due_type | block",
  "code": "POOL_01",
  "name": "Swimming Pool",
  "description": "Main pool near block A",
  "metadata": {
    "location": "Block A",
    "capacity": 50,
    "operating_hours": "06:00-21:00"
  },
  "is_active": true,
  "sort_order": 1,
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

Types:
- `facility` - Fasum (pool, mosque, park, hall, gym)
- `vehicle_brand` - Toyota, Honda, Yamaha, etc
- `gate` - Gate 1, Gate 2, etc
- `due_type` - Monthly, security, cleaning
- `block` - Block A, B, C, etc

### 9. `events`

Community events/announcements.

```json
{
  "_id": "ObjectId",
  "title": "Monthly Meeting",
  "description": "Rapat bulanan RT/RW",
  "type": "meeting | social | maintenance | emergency | announcement",
  "location": "Balai Warga",
  "start_date": "ISODate",
  "end_date": "ISODate",
  "organizer": "RT 05",
  "target_audience": "all | block_a | block_b",
  "is_mandatory": false,
  "rsvp_required": true,
  "attendees": [
    {
      "family_id": "ObjectId",
      "name": "John Doe",
      "status": "confirmed | declined | pending",
      "attended": true
    }
  ],
  "attachments": ["https://..."],
  "status": "upcoming | ongoing | completed | cancelled",
  "created_by": "admin",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

---

## Access Log (Bonus - for gate history)

### `access_logs`

Every gate entry/exit event.

```json
{
  "_id": "ObjectId",
  "gate_id": "gate_1",
  "direction": "entry | exit",
  "method": "rfid | plate_ocr | manual | guest_pass",
  "rfid_card_id": "ObjectId (ref: rfid_cards)",
  "vehicle_id": "ObjectId (ref: vehicles)",
  "plate_detected": "B 1234 XYZ",
  "plate_confidence": 0.92,
  "family_id": "ObjectId (ref: families)",
  "is_resident": true,
  "validation_result": "granted | denied_unpaid | denied_unknown | denied_expired",
  "denied_reason": "Iuran belum dibayar 2 bulan",
  "photo_url": "https://...",
  "timestamp": "ISODate"
}
```

---

## Indexes

```javascript
// vehicles - fast plate lookup
db.vehicles.createIndex({ "plate_number_normalized": 1 })

// rfid_cards - fast card scan
db.rfid_cards.createIndex({ "card_uid": 1 }, { unique: true })

// dues - check unpaid per family
db.dues.createIndex({ "family_id": 1, "status": 1, "period": -1 })

// access_logs - recent history
db.access_logs.createIndex({ "timestamp": -1 })
db.access_logs.createIndex({ "plate_detected": 1, "timestamp": -1 })

// guests - active guests
db.guests.createIndex({ "status": 1, "entry_time": -1 })

// houses - geo query
db.houses.createIndex({ "block": 1, "house_number": 1 })
```

---

## Gate Validation Flow

```
1. Vehicle arrives at gate
2. RFID scan OR Plate OCR detection
3. Lookup vehicle/card in DB
4. Check family dues status (if dues_block_enabled)
   - If unpaid > grace_period → DENIED
5. If valid → OPEN GATE + log access
6. If unknown plate → Check guest list
   - If guest found → OPEN + log
   - If not found → Alert security
```

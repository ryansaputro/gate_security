"""
Sync Dues from Google Sheet (public CSV export).

Sheet format: Nama | Blok | Nominal | Bulan | Metode
- Blok format: "B/7" → block="B", house_number="7"
- Bulan format: "2026-06"
- Metode: "Cash" or "Transfer" (default: "cash" if empty)
- Match by: house (block + house_number) → family in that house
- Status: paid (nominal > 0), sheet overwrites DB

Env vars:
  GSHEET_DUES_URL=https://docs.google.com/spreadsheets/d/SHEET_ID/gviz/tq?tqx=out:csv&sheet=SHEET_NAME
  GSHEET_SYNC_INTERVAL_MINUTES=60
"""

import os
import csv
import io
import requests
from datetime import datetime

from drivers.mongo.connection import Mongo


def sync_dues_from_gsheet():
    """Fetch Google Sheet CSV and upsert dues into MongoDB."""
    url = os.getenv("GSHEET_DUES_URL", "")
    if not url:
        print("[sync_dues_gsheet] GSHEET_DUES_URL not set, skipping")
        return {"status": "skipped", "reason": "GSHEET_DUES_URL not set"}

    # Auto-convert edit/sharing URL to CSV export URL
    if "/edit" in url or "/sharing" in url:
        # Extract sheet ID from URL like: /spreadsheets/d/SHEET_ID/edit...
        import re as _re
        match = _re.search(r'/spreadsheets/d/([^/]+)', url)
        if match:
            sheet_id = match.group(1)
            gid = "0"  # default first tab
            gid_match = _re.search(r'gid=(\d+)', url)
            if gid_match:
                gid = gid_match.group(1)
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            print(f"[sync_dues_gsheet] Auto-converted URL to CSV export")

    print(f"[sync_dues_gsheet] Fetching: {url[:80]}...")

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[sync_dues_gsheet] Failed to fetch sheet: {e}")
        return {"status": "error", "reason": str(e)}

    # Parse CSV
    content = resp.text
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    if len(rows) < 2:
        print("[sync_dues_gsheet] Sheet empty or only header")
        return {"status": "skipped", "reason": "no data rows"}

    # Find header row (first row)
    header = [h.strip().lower() for h in rows[0]]
    # Expected: nama, blok, nominal, bulan, metode
    col_map = {}
    for i, h in enumerate(header):
        if "nama" in h:
            col_map["nama"] = i
        elif "blok" in h:
            col_map["blok"] = i
        elif "nominal" in h:
            col_map["nominal"] = i
        elif "bulan" in h:
            col_map["bulan"] = i
        elif "metode" in h:
            col_map["metode"] = i

    required = ["blok", "nominal", "bulan"]
    for key in required:
        if key not in col_map:
            print(f"[sync_dues_gsheet] Missing column: {key}. Header: {header}")
            return {"status": "error", "reason": f"missing column: {key}"}

    # Connect to DB
    db = Mongo().get_db()

    # Build house → family lookup
    houses = list(db.houses.find({}, {"_id": 1, "block": 1, "houseNumber": 1}))
    house_map = {}  # "B|7" → house_id
    for h in houses:
        key = f"{h.get('block', '')}|{h.get('houseNumber', '')}"
        house_map[key] = str(h["_id"])

    families = list(db.families.find({"status": "active"}, {"_id": 1, "houseId": 1, "headName": 1}))
    house_to_family = {}  # house_id → family_id
    for f in families:
        hid = f.get("houseId", "")
        if hid:
            house_to_family[hid] = str(f["_id"])

    # Process rows
    synced = 0
    skipped = 0
    errors = []

    for row_idx, row in enumerate(rows[1:], start=2):
        try:
            if len(row) <= max(col_map.values()):
                # Row too short, pad
                row += [""] * (max(col_map.values()) + 1 - len(row))

            nama = row[col_map["nama"]].strip() if "nama" in col_map else ""
            blok_raw = row[col_map["blok"]].strip()
            nominal_raw = row[col_map["nominal"]].strip()
            bulan = row[col_map["bulan"]].strip()
            metode = row[col_map["metode"]].strip() if "metode" in col_map else ""

            # Skip empty rows
            if not blok_raw or not bulan:
                skipped += 1
                continue

            # Parse nominal
            nominal = 0
            if nominal_raw:
                # Remove dots/commas (Indonesian number format: 350.000)
                clean = nominal_raw.replace(".", "").replace(",", "").replace("Rp", "").strip()
                try:
                    nominal = int(float(clean))
                except (ValueError, TypeError):
                    nominal = 0

            if nominal <= 0:
                skipped += 1
                continue

            # Parse blok: "B/7" → block="B", house_number="7"
            if "/" in blok_raw:
                parts = blok_raw.split("/", 1)
                block = parts[0].strip().upper()
                house_number = parts[1].strip()
            else:
                block = blok_raw.strip().upper()
                house_number = ""

            # Parse bulan: "2026-06"
            year, month = 0, 0
            if "-" in bulan:
                bp = bulan.split("-")
                if len(bp) == 2 and bp[0].isdigit() and bp[1].isdigit():
                    year, month = int(bp[0]), int(bp[1])

            if not year or not month:
                skipped += 1
                continue

            # Default metode
            if not metode:
                metode = "cash"
            metode = metode.lower().strip()
            if metode not in ("cash", "transfer", "qris"):
                metode = "cash"

            # Find house → family
            house_key = f"{block}|{house_number}"
            house_id = house_map.get(house_key, "")
            family_id = house_to_family.get(house_id, "") if house_id else ""

            if not family_id:
                # Try without house_number (just block match)
                skipped += 1
                errors.append(f"Row {row_idx}: house {blok_raw} not found")
                continue

            # Upsert due: match by family_id + period
            period = f"{year:04d}-{month:02d}"
            filter_q = {
                "familyId": family_id,
                "period": period,
                "source": "gsheet",
            }
            update_doc = {
                "$set": {
                    "familyId": family_id,
                    "houseId": house_id,
                    "period": period,
                    "year": year,
                    "month": month,
                    "type": "monthly",
                    "amount": nominal,
                    "paidAmount": nominal,
                    "status": "paid",
                    "paymentMethod": metode,
                    "source": "gsheet",
                    "syncedAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow(),
                },
                "$setOnInsert": {
                    "createdAt": datetime.utcnow(),
                },
            }
            db.dues.update_one(filter_q, update_doc, upsert=True)
            synced += 1

        except Exception as e:
            errors.append(f"Row {row_idx}: {str(e)}")

    result = {
        "status": "ok",
        "synced": synced,
        "skipped": skipped,
        "errors": errors[:10],  # limit error log
        "timestamp": datetime.utcnow().isoformat(),
    }
    print(f"[sync_dues_gsheet] Done: synced={synced}, skipped={skipped}, errors={len(errors)}")
    return result

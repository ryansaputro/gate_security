"""
Cron Job: Generate Monthly Dues.

Runs on 1st of each month at 00:05.
Auto-generates dues records per block — iterates houses by block,
finds active family in each house, creates dues record.
"""

from datetime import datetime

from drivers.mongo.connection import Mongo


def run_generate_monthly_dues():
    """Generate monthly dues for all active families, grouped by block."""
    print(f"\n💰 [{datetime.now().isoformat()}] Generating monthly dues...")

    mongo = Mongo()
    db = mongo.get_db()

    now = datetime.now()
    period = f"{now.year}-{now.month:02d}"

    # Get dues amount from settings
    amount_setting = db["settings"].find_one({"key": "dues_monthly_amount"})
    amount = int(amount_setting["value"]) if amount_setting else 150000

    # Get due date from settings (day of month)
    due_day_setting = db["settings"].find_one({"key": "dues_due_day"})
    due_day = int(due_day_setting["value"]) if due_day_setting else 5

    # Get all houses grouped by block
    houses = list(db["houses"].find({}).sort([("block", 1), ("houseNumber", 1)]))

    # Build house_id → family lookup
    families = list(db["families"].find({"status": "active"}, {"_id": 1, "houseId": 1, "headName": 1}))
    house_to_family = {}
    for f in families:
        hid = f.get("houseId", "")
        if hid:
            house_to_family[hid] = f

    created_count = 0
    skipped_count = 0
    no_family_count = 0

    # Track per block for logging
    block_stats = {}

    for house in houses:
        house_id = str(house["_id"])
        block = house.get("block", "?")
        house_number = house.get("houseNumber", "?")

        if block not in block_stats:
            block_stats[block] = {"created": 0, "skipped": 0, "no_family": 0}

        # Find active family in this house
        family = house_to_family.get(house_id)
        if not family:
            no_family_count += 1
            block_stats[block]["no_family"] += 1
            continue

        family_id = str(family["_id"])

        # Check if dues already exists for this period
        existing = db["dues"].find_one({
            "familyId": family_id,
            "period": period,
            "type": "monthly",
        })

        if existing:
            skipped_count += 1
            block_stats[block]["skipped"] += 1
            continue

        # Create dues record
        db["dues"].insert_one({
            "familyId": family_id,
            "houseId": house_id,
            "period": period,
            "year": now.year,
            "month": now.month,
            "type": "monthly",
            "amount": amount,
            "paidAmount": 0,
            "status": "unpaid",
            "paidAt": None,
            "paymentMethod": "",
            "receiptNumber": "",
            "collectorName": "",
            "dueDate": datetime(now.year, now.month, due_day),
            "notes": f"Auto-generated (Blok {block}/{house_number})",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        })
        created_count += 1
        block_stats[block]["created"] += 1

    # Print summary per block
    print(f"  📊 Summary for period {period}:")
    for block in sorted(block_stats.keys()):
        s = block_stats[block]
        print(f"     Blok {block}: created={s['created']}, skipped={s['skipped']}, no_family={s['no_family']}")

    print(f"\n  ✅ Total: created={created_count}, skipped={skipped_count}, no_family={no_family_count}")
    print(f"  💵 Amount: Rp {amount:,.0f} | Due day: {due_day}")

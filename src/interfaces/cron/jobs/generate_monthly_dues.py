"""
Cron Job: Generate Monthly Dues.

Runs on 1st of each month at 00:05.
Auto-generates dues records for all active families based on settings.
"""

from datetime import datetime

from drivers.mongo.connection import Mongo


def run_generate_monthly_dues():
    """Generate monthly dues for all active families."""
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

    # Get all active families
    families = list(db["families"].find({"status": "active"}))

    created_count = 0
    skipped_count = 0

    for family in families:
        family_id = str(family["_id"])

        # Check if dues already exists for this period
        existing = db["dues"].find_one({
            "familyId": family_id,
            "period": period,
            "type": "monthly",
        })

        if existing:
            skipped_count += 1
            continue

        # Get house_id
        house_id = family.get("houseId", "")

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
            "notes": "Auto-generated",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        })
        created_count += 1

    print(f"  ✅ Created {created_count} dues for period {period}")
    if skipped_count:
        print(f"  ⏭️  Skipped {skipped_count} (already exists)")
    print(f"  💵 Amount: Rp {amount:,.0f} | Due day: {due_day}")

"""
Cron Job: Dues Payment Reminder.

Runs on 1st and 15th of each month.
Finds all families with unpaid/overdue dues and sends email notification.
"""

from datetime import datetime

from drivers.mongo.connection import Mongo
from drivers.email.sender import EmailSender
from drivers.email.templates import dues_reminder_template


def run_dues_reminder():
    """Find unpaid dues and send email reminders."""
    print(f"\n📢 [{datetime.now().isoformat()}] Running dues reminder...")

    mongo = Mongo()
    db = mongo.get_db()
    email_sender = EmailSender()

    # Check if reminder is enabled
    reminder_setting = db["settings"].find_one({"key": "dues_reminder_enabled"})
    if reminder_setting and reminder_setting.get("value") == "false":
        print("  ⏭️  Dues reminder disabled in settings")
        return

    # Get due day from settings
    due_day_setting = db["settings"].find_one({"key": "dues_due_day"})
    due_day = int(due_day_setting["value"]) if due_day_setting else 5

    # Find all unpaid/overdue dues grouped by family
    unpaid_dues = list(db["dues"].aggregate([
        {"$match": {"status": {"$in": ["unpaid", "overdue"]}}},
        {"$group": {
            "_id": "$familyId",
            "total_unpaid": {"$sum": "$amount"},
            "periods": {"$push": "$period"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
    ]))

    if not unpaid_dues:
        print("  ✅ No unpaid dues found. All clear!")
        return

    print(f"  Found {len(unpaid_dues)} families with unpaid dues")

    sent_count = 0
    failed_count = 0

    for record in unpaid_dues:
        family = db["families"].find_one({"_id": _to_object_id(record["_id"])})
        if not family:
            continue

        name = family.get("headName", "Unknown")
        phone = family.get("headPhone", "")
        email = family.get("email", "")
        total = record["total_unpaid"]
        periods = record["periods"]
        count = record["count"]

        # Send email if family has email
        email_sent = False
        if email:
            html_body = dues_reminder_template(name, periods, total, due_day)
            subject = f"Pengingat Iuran - {count} tagihan belum dibayar"
            email_sent = email_sender.send(email, subject, html_body)
            if email_sent:
                sent_count += 1
            else:
                failed_count += 1

        # Log the notification
        db["notification_logs"].insert_one({
            "family_id": record["_id"],
            "family_name": name,
            "phone": phone,
            "email": email,
            "type": "dues_reminder",
            "channel": "email" if email_sent else "logged",
            "subject": f"Pengingat Iuran - {count} tagihan",
            "total_amount": total,
            "periods": periods,
            "status": "sent" if email_sent else "no_email",
            "created_at": datetime.now(),
        })

        status_icon = "📨" if email_sent else "⚠️"
        print(f"  {status_icon} {name} ({email or 'no email'}) - {count} unpaid, Rp {total:,.0f}")

    print(f"\n  ✅ Summary: {sent_count} emails sent, {failed_count} failed, "
          f"{len(unpaid_dues) - sent_count - failed_count} no email address")


def _to_object_id(id_str):
    """Convert string to ObjectId safely."""
    from bson import ObjectId
    try:
        return ObjectId(id_str)
    except Exception:
        return id_str

"""
Cron Job: Mark Overdue Dues.

Runs daily at 01:00.
Finds all dues with status "unpaid" where dueDate has passed, updates to "overdue".
"""

from datetime import datetime

from drivers.mongo.connection import Mongo


def run_mark_overdue_dues():
    """Mark unpaid dues as overdue if past due date."""
    print(f"\n⏰ [{datetime.now().isoformat()}] Marking overdue dues...")

    db = Mongo().get_db()
    now = datetime.now()

    result = db["dues"].update_many(
        {
            "status": "unpaid",
            "dueDate": {"$lt": now, "$ne": None},
        },
        {
            "$set": {
                "status": "overdue",
                "updatedAt": now,
            }
        },
    )

    print(f"  ✅ Marked {result.modified_count} dues as overdue")
    return {"marked_overdue": result.modified_count}

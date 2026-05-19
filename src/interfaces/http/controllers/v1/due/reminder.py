"""
Trigger dues reminder manually (admin only).
"""

from fastapi import Request
from interfaces.cron.jobs.dues_reminder import run_dues_reminder


async def trigger_reminder(self, request: Request):
    """Manually trigger dues reminder job."""
    run_dues_reminder()
    return {"status": True, "message": "Dues reminder executed"}

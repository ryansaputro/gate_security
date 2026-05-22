"""
CRON Interface - Scheduled tasks.

Usage:
  INTERFACE=CRON python src/main.py

Runs all scheduled jobs using APScheduler.
"""

import os
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from interfaces.cron.jobs.dues_reminder import run_dues_reminder
from interfaces.cron.jobs.generate_monthly_dues import run_generate_monthly_dues
from interfaces.cron.jobs.mark_overdue_dues import run_mark_overdue_dues
from interfaces.cron.jobs.sync_dues_gsheet import sync_dues_from_gsheet


def launch():
    scheduler = BlockingScheduler()

    # Reminder iuran: setiap hari ke-1 dan ke-15 jam 08:00
    scheduler.add_job(
        run_dues_reminder,
        CronTrigger(day="1,15", hour=8, minute=0),
        id="dues_reminder",
        name="Dues Payment Reminder",
    )

    # Generate iuran bulanan: setiap tanggal 1 jam 00:05
    scheduler.add_job(
        run_generate_monthly_dues,
        CronTrigger(day=1, hour=0, minute=5),
        id="generate_monthly_dues",
        name="Generate Monthly Dues",
    )

    # Mark overdue dues: setiap hari jam 01:00
    scheduler.add_job(
        run_mark_overdue_dues,
        CronTrigger(hour=1, minute=0),
        id="mark_overdue_dues",
        name="Mark Overdue Dues",
    )

    # Sync dues from Google Sheet
    sync_interval = int(os.getenv("GSHEET_SYNC_INTERVAL_MINUTES", "60"))
    if os.getenv("GSHEET_DUES_URL"):
        scheduler.add_job(
            sync_dues_from_gsheet,
            IntervalTrigger(minutes=sync_interval),
            id="sync_dues_gsheet",
            name=f"Sync Dues from GSheet (every {sync_interval}min)",
        )
        # Also run once on startup (after 10s delay)
        scheduler.add_job(
            sync_dues_from_gsheet,
            "date",
            run_date=None,  # run immediately
            id="sync_dues_gsheet_startup",
            name="Sync Dues from GSheet (startup)",
        )

    def shutdown(signum, frame):
        print("\n🛑 Shutting down scheduler...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("⏰ CRON scheduler started")
    print("   Jobs:")
    for job in scheduler.get_jobs():
        print(f"   - {job.name} ({job.trigger})")
    print()

    scheduler.start()

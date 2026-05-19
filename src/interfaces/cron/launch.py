"""
CRON Interface - Scheduled tasks.

Usage:
  INTERFACE=CRON python src/main.py

Runs all scheduled jobs using APScheduler.
"""

import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from interfaces.cron.jobs.dues_reminder import run_dues_reminder
from interfaces.cron.jobs.generate_monthly_dues import run_generate_monthly_dues


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

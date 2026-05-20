#!/usr/bin/env python3
"""
Seed admin users for the web admin panel.

Usage:
  python3 src/scripts/seed_admins.py

Default accounts:
  - admin / admin123 (superadmin)
  - security / security123 (security)
"""

import os
import sys
import hashlib
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from drivers.mongo.connection import Mongo


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed():
    mongo = Mongo()
    db = mongo.get_db()

    admins = [
        {
            "username": "admin",
            "name": "Administrator",
            "password_hash": hash_password("admin123"),
            "role": "superadmin",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "username": "security",
            "name": "Security Guard",
            "password_hash": hash_password("security123"),
            "role": "security",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    ]

    for admin in admins:
        existing = db.admins.find_one({"username": admin["username"]})
        if existing:
            print(f"  [SKIP] {admin['username']} already exists")
        else:
            db.admins.insert_one(admin)
            print(f"  [OK] Created {admin['username']} ({admin['role']})")

    # Create unique index on username
    db.admins.create_index("username", unique=True)
    print("\n  Done! Login at http://localhost:3000/admin/login")
    print("  Default: admin / admin123")

    mongo.close()


if __name__ == "__main__":
    print("=" * 40)
    print("  Seeding Admin Users")
    print("=" * 40)
    seed()

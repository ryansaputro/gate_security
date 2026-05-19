"""
Seed initial admin API key.

Usage:
    python src/scripts/seed_api_key.py

This creates the first admin key so you can bootstrap the system.
Run once, save the key, then use it to create more keys via API.
"""

import os
import sys
import secrets
import hashlib
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from drivers.mongo.connection import Mongo


def main():
    mongo = Mongo()
    db = mongo.get_db()

    # Generate admin key
    raw_key = f"gsk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    doc = {
        "name": "initial-admin",
        "role": "admin",
        "key_hash": key_hash,
        "key_prefix": raw_key[:8],
        "is_active": True,
        "created_at": datetime.now(),
        "last_used_at": None,
        "expires_at": None,
    }

    db["api_keys"].insert_one(doc)

    print("=" * 60)
    print("  ADMIN API KEY CREATED")
    print("=" * 60)
    print(f"  Key: {raw_key}")
    print(f"  Role: admin")
    print(f"  Name: initial-admin")
    print("=" * 60)
    print("  ⚠️  Save this key! It won't be shown again.")
    print("=" * 60)

    # Also create a device key for the gate client
    device_key = f"gsk_{secrets.token_urlsafe(32)}"
    device_hash = hashlib.sha256(device_key.encode()).hexdigest()

    db["api_keys"].insert_one({
        "name": "gate-1-device",
        "role": "device",
        "key_hash": device_hash,
        "key_prefix": device_key[:8],
        "is_active": True,
        "created_at": datetime.now(),
        "last_used_at": None,
        "expires_at": None,
    })

    print()
    print("=" * 60)
    print("  DEVICE API KEY CREATED")
    print("=" * 60)
    print(f"  Key: {device_key}")
    print(f"  Role: device")
    print(f"  Name: gate-1-device")
    print("=" * 60)
    print("  Use this in GATE_API_KEY env var for gate client.")
    print("=" * 60)

    # Create index
    db["api_keys"].create_index("key_hash", unique=True)
    print("\n✅ Index created on api_keys.key_hash")


if __name__ == "__main__":
    main()

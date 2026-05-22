"""
Telegram Handler: Admin Panel (/admin).

Flow:
1. /admin → bot minta username
2. User kirim username
3. Bot minta password
4. User kirim password → verify against admins collection (same as web)
5. If valid → show menu: 1. Lihat request pending, 2. Approve request
"""

import os
import hashlib
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from drivers.mongo.connection import Mongo

# Conversation states
ADMIN_USERNAME = 20
ADMIN_PASSWORD = 21
ADMIN_MENU = 22
ADMIN_APPROVE = 23


def _hash_password(password: str) -> str:
    """SHA256 hash — same as web admin."""
    return hashlib.sha256(password.encode()).hexdigest()


async def start_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: /admin command."""
    # Check if already logged in this session
    if context.user_data.get("admin_logged_in"):
        return await _show_admin_menu(update, context)

    await update.message.reply_text("Login Admin\n\nKirim username:")
    return ADMIN_USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive admin username."""
    context.user_data["admin_username"] = update.message.text.strip()
    await update.message.reply_text("Kirim password:")
    return ADMIN_PASSWORD


async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive password and verify."""
    password = update.message.text.strip()
    username = context.user_data.get("admin_username", "")

    db = Mongo().get_db()
    admin = db.admins.find_one({"username": username, "is_active": True})

    if not admin or admin.get("password_hash") != _hash_password(password):
        await update.message.reply_text("Username atau password salah.\n\nGunakan /admin untuk coba lagi.")
        context.user_data.clear()
        return ConversationHandler.END

    # Login success
    context.user_data["admin_logged_in"] = True
    context.user_data["admin_name"] = admin.get("name", username)
    return await _show_admin_menu(update, context)


async def _show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu."""
    name = context.user_data.get("admin_name", "Admin")
    await update.message.reply_text(
        f"Halo {name}!\n\n"
        "1. Lihat request pending\n"
        "2. Approve request\n"
        "3. Logout\n\n"
        "Kirim angka:"
    )
    return ADMIN_MENU


async def admin_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu choice."""
    text = update.message.text.strip()

    if text == "1":
        return await _show_pending(update, context)
    elif text == "2":
        return await _show_pending_for_approve(update, context)
    elif text == "3":
        context.user_data.clear()
        await update.message.reply_text("Logged out.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Pilih 1, 2, atau 3.")
        return ADMIN_MENU


async def _show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all pending bindings."""
    db = Mongo().get_db()
    pendings = list(db.telegram_bindings.find({"status": "pending"}).sort("requestedAt", -1).limit(20))

    if not pendings:
        await update.message.reply_text("Tidak ada request pending.\n\nGunakan /admin untuk kembali.")
        return ConversationHandler.END

    lines = []
    for i, b in enumerate(pendings, 1):
        family = db.families.find_one({"_id": _to_oid(b.get("familyId", ""))})
        name = family.get("headName", "?") if family else "?"
        house_label = "-"
        if family and family.get("houseId"):
            house = db.houses.find_one({"_id": _to_oid(family["houseId"])})
            if house:
                house_label = f"Blok {house.get('block', '')} No.{house.get('houseNumber', '')}"
        tg_name = b.get("telegramFirstName", "?")
        lines.append(f"{i}. {name} ({house_label}) — TG: {tg_name}")

    msg = f"Request Pending ({len(pendings)}):\n\n" + "\n".join(lines)
    msg += "\n\nGunakan /admin untuk kembali."
    await update.message.reply_text(msg)
    return ConversationHandler.END


async def _show_pending_for_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending list and ask which to approve."""
    db = Mongo().get_db()
    pendings = list(db.telegram_bindings.find({"status": "pending"}).sort("requestedAt", -1).limit(20))

    if not pendings:
        await update.message.reply_text("Tidak ada request pending untuk di-approve.")
        return ConversationHandler.END

    lines = []
    for i, b in enumerate(pendings, 1):
        family = db.families.find_one({"_id": _to_oid(b.get("familyId", ""))})
        name = family.get("headName", "?") if family else "?"
        house_label = "-"
        if family and family.get("houseId"):
            house = db.houses.find_one({"_id": _to_oid(family["houseId"])})
            if house:
                house_label = f"Blok {house.get('block', '')} No.{house.get('houseNumber', '')}"
        lines.append(f"{i}. {name} ({house_label})")

    # Store pendings in context for approval
    context.user_data["admin_pendings"] = [
        {"id": str(b["_id"]), "telegram_id": b.get("telegramId")}
        for b in pendings
    ]

    msg = "Pilih nomor yang mau di-approve:\n\n" + "\n".join(lines)
    msg += "\n\nKirim nomor (misal: 1):"
    await update.message.reply_text(msg)
    return ADMIN_APPROVE


async def admin_approve_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a binding by number."""
    import requests as req

    text = update.message.text.strip()
    pendings = context.user_data.get("admin_pendings", [])

    if not text.isdigit():
        await update.message.reply_text("Kirim nomor yang valid.")
        return ADMIN_APPROVE

    idx = int(text) - 1
    if idx < 0 or idx >= len(pendings):
        await update.message.reply_text(f"Nomor harus 1-{len(pendings)}.")
        return ADMIN_APPROVE

    binding_info = pendings[idx]
    db = Mongo().get_db()

    # Approve
    db.telegram_bindings.update_one(
        {"_id": _to_oid(binding_info["id"]), "status": "pending"},
        {"$set": {
            "status": "approved",
            "approvedAt": datetime.utcnow(),
            "approvedBy": "telegram_admin",
        }},
    )

    # Notify user
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if token and binding_info.get("telegram_id"):
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            req.post(url, json={
                "chat_id": binding_info["telegram_id"],
                "text": "Pendaftaran Anda telah disetujui! Sekarang bisa gunakan /tagihan.",
            }, timeout=10)
        except Exception:
            pass

    await update.message.reply_text("Approved! User sudah dinotifikasi.\n\nGunakan /admin untuk kembali.")
    context.user_data.clear()
    return ConversationHandler.END


def _to_oid(id_str):
    from bson import ObjectId
    try:
        return ObjectId(id_str)
    except Exception:
        return id_str

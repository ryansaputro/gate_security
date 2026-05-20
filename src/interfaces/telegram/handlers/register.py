"""
Telegram Handler: Register Telegram ID Binding (/daftar).

Flow:
1. User sends /daftar
2. Bot asks: nama + blok (e.g. "Ryan B/7")
3. User replies with name/block
4. Bot searches families using same logic as check_dues
5. If found exactly 1 → create binding with status "pending"
6. If found multiple → ask user to be more specific
7. If found 0 → tell user not found
"""

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from drivers.mongo.connection import Mongo
from interfaces.telegram.handlers.check_dues import _parse_input, _search_families

# Conversation states
WAITING_REGISTER_INPUT = 10


async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: /daftar command."""
    user = update.effective_user
    db = Mongo().get_db()

    # Check if user already has an approved or pending binding
    existing = db.telegram_bindings.find_one({
        "telegramId": user.id,
        "status": {"$in": ["pending", "approved"]},
    })

    if existing:
        if existing["status"] == "approved":
            await update.message.reply_text(
                "✅ Akun Telegram Anda sudah terdaftar dan disetujui.\n"
                "Gunakan /tagihan untuk cek tagihan."
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "⏳ Pendaftaran Anda masih menunggu approval admin.\n"
                "Silakan tunggu konfirmasi."
            )
            return ConversationHandler.END

    await update.message.reply_text(
        "📝 *Pendaftaran Akun Telegram*\n\n"
        "Silakan kirim nama kepala keluarga + blok rumah.\n"
        "Contoh: `Ryan B/7` atau `Budi Blok A No 10`\n\n"
        "Pastikan sesuai data yang terdaftar di sistem.",
        parse_mode="Markdown",
    )
    return WAITING_REGISTER_INPUT


async def receive_register_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive name/block input for registration."""
    text = update.message.text.strip()
    user = update.effective_user

    if not text:
        await update.message.reply_text("❌ Input kosong. Silakan kirim nama + blok.")
        return WAITING_REGISTER_INPUT

    # Search families
    try:
        families = _search_families(text)
    except Exception as e:
        print(f"❌ Error searching families for registration: {e}")
        await update.message.reply_text(f"❌ Terjadi error: {e}")
        return WAITING_REGISTER_INPUT

    if not families:
        await update.message.reply_text(
            f"❌ Tidak ditemukan warga dengan pencarian: *{text}*\n\n"
            "Pastikan nama dan blok sesuai data yang terdaftar.\n"
            "Coba kirim ulang atau hubungi admin.",
            parse_mode="Markdown",
        )
        return WAITING_REGISTER_INPUT

    if len(families) > 1:
        # Multiple matches — ask to be more specific
        family_list = ""
        for i, fam in enumerate(families[:10], 1):
            family_list += f"{i}. {fam['head_name']} — {fam['house_label']}\n"

        await update.message.reply_text(
            f"⚠️ Ditemukan {len(families)} keluarga:\n\n"
            f"{family_list}\n"
            "Mohon kirim lebih spesifik (nama lengkap + blok/nomor).",
            parse_mode="Markdown",
        )
        return WAITING_REGISTER_INPUT

    # Exactly 1 match — create binding
    family = families[0]
    db = Mongo().get_db()

    # Check if this family already has an approved binding
    existing_family_binding = db.telegram_bindings.find_one({
        "familyId": family["id"],
        "status": "approved",
    })

    if existing_family_binding:
        await update.message.reply_text(
            "⚠️ Keluarga ini sudah terdaftar oleh akun Telegram lain.\n"
            "Hubungi admin jika ini adalah kesalahan."
        )
        return ConversationHandler.END

    # Create pending binding
    binding = {
        "telegramId": user.id,
        "telegramUsername": user.username or "",
        "telegramFirstName": user.first_name or "",
        "familyId": family["id"],
        "status": "pending",
        "requestedAt": datetime.utcnow(),
        "approvedAt": None,
        "approvedBy": None,
    }
    db.telegram_bindings.insert_one(binding)

    await update.message.reply_text(
        f"✅ Pendaftaran dikirim ke admin.\n\n"
        f"Nama: *{family['head_name']}*\n"
        f"Rumah: {family['house_label']}\n\n"
        "Tunggu konfirmasi ya. Setelah disetujui, "
        "Anda bisa langsung cek tagihan dengan /tagihan tanpa perlu input nama lagi.",
        parse_mode="Markdown",
    )

    context.user_data.clear()
    return ConversationHandler.END

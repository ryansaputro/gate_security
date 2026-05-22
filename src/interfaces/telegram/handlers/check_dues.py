"""
Telegram Handler: Check Dues (Cek Tagihan Iuran).

Flow (with Telegram binding):
1. User sends /tagihan
2. Bot checks if user has approved binding
   - If approved → ask period directly
   - If pending → tell user to wait
   - If not registered → tell user to use /daftar
3. User replies with period (e.g. "mei 2025" or "semua")
4. Bot returns dues info
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from usecases.due.interface import DueUsecase
from usecases.family.interface import FamilyUsecase
from usecases.house.interface import HouseUsecase
from drivers.mongo.connection import Mongo

# Conversation states
WAITING_NAME = 0
WAITING_PERIOD = 1

# Month name mapping (Indonesian)
MONTH_NAMES = {
    "januari": 1, "jan": 1,
    "februari": 2, "feb": 2,
    "maret": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "ags": 8,
    "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "desember": 12, "des": 12,
}


async def start_check_dues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: /tagihan command. Check binding first."""
    user = update.effective_user
    db = Mongo().get_db()

    # Check telegram binding — prioritize approved, then pending, then rejected
    binding = db.telegram_bindings.find_one(
        {"telegramId": user.id, "status": "approved"}
    )
    if not binding:
        binding = db.telegram_bindings.find_one(
            {"telegramId": user.id, "status": "pending"}
        )
    if not binding:
        binding = db.telegram_bindings.find_one(
            {"telegramId": user.id, "status": "rejected"}
        )

    if binding:
        if binding["status"] == "approved":
            # User is registered — get family info and ask for period
            family_id = binding["familyId"]
            family = db.families.find_one({"_id": _to_oid(family_id)})

            if not family:
                await update.message.reply_text(
                    "❌ Data keluarga tidak ditemukan. Hubungi admin."
                )
                return ConversationHandler.END

            # Get house label
            house_label = "-"
            if family.get("houseId"):
                house = db.houses.find_one({"_id": _to_oid(family["houseId"])})
                if house:
                    house_label = f"Blok {house.get('block', '')} No.{house.get('houseNumber', '')}"

            # Store family in context
            context.user_data["matched_families"] = [{
                "id": str(family["_id"]),
                "head_name": family.get("headName", ""),
                "house_id": family.get("houseId", ""),
                "house_label": house_label,
            }]

            await update.message.reply_text(
                f"👋 Halo *{family.get('headName', '')}* ({house_label})\n\n"
                "Kirim periode yang ingin dicek:\n"
                "• Bulan tahun: `mei 2025` atau `2025-05`\n"
                "• Tahun saja: `2025`\n"
                "• Ketik `semua` untuk semua periode",
                parse_mode="Markdown",
            )
            return WAITING_PERIOD

        elif binding["status"] == "pending":
            await update.message.reply_text(
                "⏳ Pendaftaran masih menunggu approval admin.\n"
                "Silakan tunggu konfirmasi dari admin."
            )
            return ConversationHandler.END

        elif binding["status"] == "rejected":
            await update.message.reply_text(
                "❌ Pendaftaran Anda ditolak oleh admin.\n"
                "Gunakan /daftar untuk mendaftar ulang."
            )
            return ConversationHandler.END

    # Not registered
    await update.message.reply_text(
        "❌ Anda belum terdaftar. Gunakan /daftar untuk mendaftar.\n\n"
        "Setelah disetujui admin, Anda bisa langsung cek tagihan tanpa input nama."
    )
    return ConversationHandler.END


async def receive_name_or_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive name/block input, search families, ask for period."""
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Input kosong. Silakan kirim nama atau blok.")
        return WAITING_NAME

    # Search families by name or block
    try:
        families = _search_families(text)
    except Exception as e:
        print(f"❌ Error searching families: {e}")
        await update.message.reply_text(f"❌ Terjadi error: {e}")
        return WAITING_NAME

    if not families:
        await update.message.reply_text(
            f"❌ Tidak ditemukan warga dengan pencarian: *{text}*\n\n"
            "Coba kirim ulang dengan nama atau blok yang benar.",
            parse_mode="Markdown",
        )
        return WAITING_NAME

    # Store matched families in context for next step
    context.user_data["matched_families"] = families
    context.user_data["search_text"] = text

    # Show matched families
    family_list = ""
    for i, fam in enumerate(families[:10], 1):
        family_list += f"{i}. {fam['head_name']} — {fam['house_label']}\n"

    if len(families) > 10:
        family_list += f"\n_(+{len(families) - 10} lainnya)_"

    await update.message.reply_text(
        f"✅ Ditemukan {len(families)} keluarga:\n\n"
        f"{family_list}\n\n"
        "Sekarang kirim periode yang ingin dicek:\n"
        "• Bulan tahun: `mei 2025` atau `2025-05`\n"
        "• Tahun saja: `2025`\n"
        "• Ketik `semua` untuk semua periode",
        parse_mode="Markdown",
    )
    return WAITING_PERIOD


async def receive_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive period input, query dues, return result."""
    text = update.message.text.strip().lower()
    families = context.user_data.get("matched_families", [])

    if not families:
        await update.message.reply_text("❌ Sesi expired. Silakan mulai lagi dengan /tagihan")
        return ConversationHandler.END

    # Parse period
    year, month = _parse_period(text)

    # Get family IDs
    family_ids = [f["id"] for f in families]

    # Query dues
    due_uc = DueUsecase()
    dues, _, _, total = due_uc.list(
        family_ids=family_ids,
        year=year if year else None,
        month=month if month else None,
        per_page=50,
    )

    if not dues:
        period_label = _format_period_label(year, month, text)
        await update.message.reply_text(
            f"✅ Tidak ada tagihan {period_label} untuk warga yang dicari.\n\n"
            "Gunakan /tagihan untuk cek lagi.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # Format response
    response = _format_dues_response(dues, families, year, month, text)
    await update.message.reply_text(response, parse_mode="Markdown")

    # Clear context
    context.user_data.clear()
    return ConversationHandler.END


def _search_families(text: str) -> list:
    """
    Search families by name and/or block.
    
    Input formats:
    - "Ryan B/7" → cari block B no 7, filter headName contains "Ryan"
    - "Ryan" → cari semua family yang headName contains "Ryan"
    - "B/7" → cari semua family di block B no 7
    - "B" → cari semua family di block B
    """
    from drivers.mongo.connection import Mongo
    db = Mongo().get_db()

    # Try to split input into name + block parts
    name_part, block, house_number = _parse_input(text)

    families_found = []

    if block:
        # Step 1: Find houses by block
        house_query = {"block": {"$regex": f"^{block}$", "$options": "i"}}
        if house_number:
            house_query["houseNumber"] = {"$regex": f"^{house_number}$", "$options": "i"}

        houses = list(db.houses.find(house_query))
        house_ids = [str(h["_id"]) for h in houses]
        house_map = {str(h["_id"]): f"Blok {h.get('block', '')} No.{h.get('houseNumber', '')}" for h in houses}

        if house_ids:
            # Step 2: Find families in those houses
            fam_query = {"houseId": {"$in": house_ids}, "status": "active"}

            # Step 3: If name provided, filter by headName too
            if name_part:
                fam_query["headName"] = {"$regex": name_part, "$options": "i"}

            fams = list(db.families.find(fam_query))

            for f in fams:
                families_found.append({
                    "id": str(f["_id"]),
                    "head_name": f.get("headName", ""),
                    "house_id": f.get("houseId", ""),
                    "house_label": house_map.get(f.get("houseId", ""), "-"),
                })
    elif name_part:
        # No block provided, search by name only
        fams = list(db.families.find({
            "headName": {"$regex": name_part, "$options": "i"},
            "status": "active",
        }))

        for f in fams:
            house_label = "-"
            if f.get("houseId"):
                house = db.houses.find_one({"_id": _to_oid(f["houseId"])})
                if house:
                    house_label = f"Blok {house.get('block', '')} No.{house.get('houseNumber', '')}"
            families_found.append({
                "id": str(f["_id"]),
                "head_name": f.get("headName", ""),
                "house_id": f.get("houseId", ""),
                "house_label": house_label,
            })

    return families_found


def _parse_input(text: str) -> tuple:
    """
    Parse user input into (name_part, block, house_number).
    
    Examples:
    - "Ryan B/7" → ("Ryan", "B", "7")
    - "Ryan Saputro B/7" → ("Ryan Saputro", "B", "7")
    - "B/7" → ("", "B", "7")
    - "Ryan" → ("Ryan", None, None)
    - "Blok A No 10" → ("", "A", "10")
    - "Ryan Blok A No 10" → ("Ryan", "A", "10")
    """
    import re
    text = text.strip()

    # Pattern: letter(s)/number at end — "B/7", "AB-12"
    m = re.search(r'\b([A-Za-z]{1,2})[/\-](\d+)\s*$', text)
    if m:
        block = m.group(1).upper()
        house_number = m.group(2)
        name_part = text[:m.start()].strip()
        return name_part, block, house_number

    # Pattern: "Blok X No Y" anywhere
    m = re.search(r'[Bb]lok\s+([A-Za-z]+)\s+[Nn]o\.?\s*(\d+)', text)
    if m:
        block = m.group(1).upper()
        house_number = m.group(2)
        name_part = text[:m.start()].strip()
        return name_part, block, house_number

    # Pattern: single letter + number at end "... A 7"
    m = re.search(r'\b([A-Za-z])\s+(\d+)\s*$', text)
    if m:
        block = m.group(1).upper()
        house_number = m.group(2)
        name_part = text[:m.start()].strip()
        return name_part, block, house_number

    # Pattern: just block letter at end (1-2 chars) — only if entire input is 1-2 chars
    if len(text) <= 2 and text.isalpha():
        return "", text.upper(), None

    # No block found — treat entire input as name
    return text, None, None


def _parse_period(text: str) -> tuple:
    """Parse period text. Returns (year, month) — either can be 0/None."""
    import re

    if text in ("semua", "all", "semua periode"):
        return 0, 0

    # Pattern: "2025-05" or "05-2025"
    m = re.match(r"^(\d{4})-(\d{1,2})$", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = re.match(r"^(\d{1,2})-(\d{4})$", text)
    if m:
        return int(m.group(2)), int(m.group(1))

    # Pattern: "mei 2025" or "2025 mei"
    for month_name, month_num in MONTH_NAMES.items():
        if month_name in text:
            year_match = re.search(r"(\d{4})", text)
            year = int(year_match.group(1)) if year_match else 0
            return year, month_num

    # Pattern: just year "2025"
    m = re.match(r"^(\d{4})$", text)
    if m:
        return int(m.group(1)), 0

    return 0, 0


def _format_period_label(year: int, month: int, raw: str) -> str:
    """Format period for display."""
    if year and month:
        month_names_id = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        return f"{month_names_id[month]} {year}"
    if year:
        return f"tahun {year}"
    return f"({raw})"


def _format_dues_response(dues: list, families: list, year: int, month: int, raw_period: str) -> str:
    """Format dues list into Telegram message."""
    due_uc = DueUsecase()
    family_map = {f["id"]: f for f in families}

    period_label = _format_period_label(year, month, raw_period)
    header = f"📊 *Tagihan Iuran {period_label}*\n\n"

    total_amount = 0
    total_paid = 0
    lines = []

    for due in dues[:20]:
        serialized = due_uc.serialize(due)
        fam = family_map.get(serialized.get("family_id", ""), {})
        name = fam.get("head_name", "?")
        house = fam.get("house_label", "-")

        status_icon = "✅" if serialized["status"] == "paid" else "❌"
        amount = serialized.get("amount", 0)
        paid = serialized.get("paid_amount", 0)
        period = serialized.get("period", "-")

        total_amount += amount
        total_paid += paid

        line = f"{status_icon} *{name}* ({house})\n"
        line += f"    Periode: {period} | Rp {amount:,.0f}"
        if serialized["status"] == "paid":
            line += " ✓"
        elif paid > 0:
            line += f" (dibayar: Rp {paid:,.0f})"
        lines.append(line)

    body = "\n".join(lines)

    footer = f"\n\n📌 *Ringkasan:*\n"
    footer += f"Total tagihan: Rp {total_amount:,.0f}\n"
    footer += f"Total dibayar: Rp {total_paid:,.0f}\n"
    remaining = total_amount - total_paid
    if remaining > 0:
        footer += f"Sisa: Rp {remaining:,.0f}"
    else:
        footer += "🎉 Lunas semua!"

    if len(dues) > 20:
        footer += f"\n\n_(Menampilkan 20 dari {len(dues)} tagihan)_"

    footer += "\n\nGunakan /tagihan untuk cek lagi."

    return header + body + footer


def _to_oid(id_str):
    """Convert string to ObjectId safely."""
    from bson import ObjectId
    try:
        return ObjectId(id_str)
    except Exception:
        return id_str

"""
Telegram Bot Interface - Launch.

Commands:
  /start - Welcome message
  /daftar - Register Telegram ID to family
  /tagihan - Check dues (requires registration)
  /help - Show available commands
"""

import os
import asyncio
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from interfaces.telegram.handlers.check_dues import (
    start_check_dues,
    receive_period,
    WAITING_PERIOD,
)
from interfaces.telegram.handlers.register import (
    start_register,
    receive_register_input,
    WAITING_REGISTER_INPUT,
)
from interfaces.telegram.handlers.admin import (
    start_admin,
    receive_username,
    receive_password,
    admin_menu_choice,
    admin_approve_choice,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    ADMIN_MENU,
    ADMIN_APPROVE,
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Saya bot informasi iuran warga.\n\n"
        "/daftar - Daftarkan akun\n"
        "/tagihan - Cek tagihan iuran\n"
        "/help - Bantuan"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Perintah yang tersedia:\n\n"
        "/daftar - Daftarkan akun Telegram\n"
        "/tagihan - Cek tagihan iuran\n"
        "/help - Tampilkan bantuan\n\n"
        "Daftar dulu dengan /daftar, setelah admin approve "
        "bisa langsung /tagihan."
    )


def launch():
    """Start the Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("TELEGRAM_BOT_TOKEN not set. Cannot start bot.")
        return

    print("Starting Telegram bot...")

    app = ApplicationBuilder().token(token).build()

    # /daftar conversation
    daftar_handler = ConversationHandler(
        entry_points=[CommandHandler("daftar", start_register)],
        states={
            WAITING_REGISTER_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_register_input)
            ],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
    )

    # /tagihan conversation
    tagihan_handler = ConversationHandler(
        entry_points=[CommandHandler("tagihan", start_check_dues)],
        states={
            WAITING_PERIOD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_period)
            ],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(daftar_handler)
    app.add_handler(tagihan_handler)

    # /admin conversation
    admin_handler = ConversationHandler(
        entry_points=[CommandHandler("admin", start_admin)],
        states={
            ADMIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
            ADMIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
            ADMIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu_choice)],
            ADMIN_APPROVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_approve_choice)],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
    )
    app.add_handler(admin_handler)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _run():
        async with app:
            await app.bot.set_my_commands([
                BotCommand("start", "Mulai"),
                BotCommand("daftar", "Daftarkan akun"),
                BotCommand("tagihan", "Cek tagihan"),
                BotCommand("admin", "Admin panel"),
                BotCommand("help", "Bantuan"),
            ])
            print("Bot commands registered")
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            await app.start()
            print("Bot polling started")
            while True:
                await asyncio.sleep(1)

    try:
        loop.run_until_complete(_run())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        loop.close()

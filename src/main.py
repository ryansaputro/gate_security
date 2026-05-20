"""
Main entry point (mirrors basecode-golang src/main.go).

Usage:
  HTTP:     INTERFACE=HTTP python src/main.py
  CMD:      INTERFACE=CMD python src/main.py -- --device 0 --interval 3
  Or:       uvicorn interfaces.http.launch:app --reload --port 3000
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def main():
    app_interface = os.getenv("INTERFACE", "HTTP")

    if app_interface == "HTTP":
        import uvicorn
        port = int(os.getenv("HTTP_PORT", "3000"))

        # Start Telegram bot in background if token is set
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if telegram_token:
            try:
                import threading
                from interfaces.telegram.launch import launch as launch_telegram
                bot_thread = threading.Thread(target=launch_telegram, daemon=True)
                bot_thread.start()
                print(f"🤖 Telegram bot started in background")
            except ImportError:
                print("⚠️  python-telegram-bot not installed. Skipping Telegram bot.")
                print("   Install with: pip3 install --break-system-packages python-telegram-bot")

        # IMPORTANT: reload=False when telegram bot is running to avoid duplicate bot instances
        use_reload = os.getenv("ENVIRONMENT", "dev") != "production" and not telegram_token
        uvicorn.run(
            "interfaces.http.launch:app",
            host="0.0.0.0",
            port=port,
            reload=use_reload,
        )
    elif app_interface == "CMD":
        from interfaces.cmd.launch import launch
        launch()
    elif app_interface == "CRON":
        from interfaces.cron.launch import launch
        launch()
    elif app_interface == "TELEGRAM":
        from interfaces.telegram.launch import launch
        launch()
    else:
        print(f"Interface not found: {app_interface}")
        sys.exit(1)


if __name__ == "__main__":
    main()

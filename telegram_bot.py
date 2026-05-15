#!/usr/bin/env python3
"""Telegram Bot for Guest WiFi Timer override control.

Allows authorized users to extend guest WiFi beyond the schedule
via inline buttons. Writes an override.json that guest_wifi_timer.py respects.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

SCRIPT_DIR = Path(__file__).resolve().parent
OVERRIDE_FILE = SCRIPT_DIR / "override.json"

logging.basicConfig(
    format="%(asctime)s [TelegramBot] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DURATIONS = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]


def format_duration(hours):
    if hours == int(hours):
        return f"{int(hours)}h"
    return f"{hours:.1f}h".replace(".", ",")


def build_keyboard():
    buttons = []
    row = []
    for h in DURATIONS:
        row.append(InlineKeyboardButton(f"+{format_duration(h)}", callback_data=f"override_{h}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Override aufheben", callback_data="override_cancel")])
    return InlineKeyboardMarkup(buttons)


def read_override():
    if not OVERRIDE_FILE.exists():
        return None
    try:
        with open(OVERRIDE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def write_override(until_dt):
    data = {"until": until_dt.isoformat(), "created": datetime.now().isoformat()}
    with open(OVERRIDE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def cancel_override():
    if OVERRIDE_FILE.exists():
        OVERRIDE_FILE.unlink()
        return True
    return False


def status_text():
    override = read_override()
    if not override:
        return "Kein Override aktiv. Normaler Zeitplan gilt."
    try:
        until = datetime.fromisoformat(override["until"])
    except (KeyError, ValueError):
        return "Override-Datei fehlerhaft."
    if datetime.now() >= until:
        cancel_override()
        return "Override war abgelaufen und wurde entfernt."
    remaining = until - datetime.now()
    minutes = int(remaining.total_seconds() / 60)
    return f"Override aktiv bis {until.strftime('%H:%M')} (noch {minutes} Min.)"


def check_authorized(user_id, allowed_ids):
    return user_id in allowed_ids


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allowed = context.bot_data.get("allowed_users", set())
    if not check_authorized(update.effective_user.id, allowed):
        await update.message.reply_text("Nicht autorisiert.")
        return
    text = f"Gast-WLAN Override\n\n{status_text()}\n\nWie lange soll das WLAN AN bleiben?"
    await update.message.reply_text(text, reply_markup=build_keyboard())


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allowed = context.bot_data.get("allowed_users", set())
    if not check_authorized(update.effective_user.id, allowed):
        await update.message.reply_text("Nicht autorisiert.")
        return
    await update.message.reply_text(status_text())


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    allowed = context.bot_data.get("allowed_users", set())
    if not check_authorized(query.from_user.id, allowed):
        await query.edit_message_text("Nicht autorisiert.")
        return

    data = query.data

    if data == "override_cancel":
        if cancel_override():
            log.info("Override aufgehoben von %s", query.from_user.first_name)
            text = "Override aufgehoben. Normaler Zeitplan gilt wieder."
        else:
            text = "Kein Override aktiv."
        await query.edit_message_text(text, reply_markup=build_keyboard())
        return

    if data.startswith("override_"):
        hours = float(data.replace("override_", ""))
        until = datetime.now() + timedelta(hours=hours)
        write_override(until)
        log.info("Override gesetzt: +%sh bis %s von %s", hours, until.strftime("%H:%M"), query.from_user.first_name)
        text = f"Gast-WLAN bleibt AN bis {until.strftime('%H:%M')} (+{format_duration(hours)})"
        await query.edit_message_text(text, reply_markup=build_keyboard())


def main():
    load_dotenv(SCRIPT_DIR / ".env")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("FEHLER: TELEGRAM_BOT_TOKEN nicht gesetzt in .env")
        sys.exit(1)

    allowed_raw = os.getenv("TELEGRAM_ALLOWED_USERS", "")
    if not allowed_raw:
        print("FEHLER: TELEGRAM_ALLOWED_USERS nicht gesetzt in .env")
        sys.exit(1)

    allowed_users = set()
    for uid in allowed_raw.split(","):
        uid = uid.strip()
        if uid:
            allowed_users.add(int(uid))

    log.info("Bot startet. Autorisierte User-IDs: %s", allowed_users)

    app = ApplicationBuilder().token(token).build()
    app.bot_data["allowed_users"] = allowed_users

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()


if __name__ == "__main__":
    main()

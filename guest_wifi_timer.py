#!/usr/bin/env python3
"""Guest WiFi Timer for Fritz!Box 7590.

Reads a weekly schedule from schedule.yaml and enables/disables
the Fritz!Box guest WiFi accordingly via TR-064 API.
Designed to run as a cron job (every minute).
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fritzconnection.lib.fritzwlan import FritzGuestWLAN

SCRIPT_DIR = Path(__file__).resolve().parent
DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def load_schedule():
    """Load the weekly schedule from schedule.yaml."""
    schedule_path = SCRIPT_DIR / "schedule.yaml"
    with open(schedule_path, "r") as f:
        config = yaml.safe_load(f)
    return config["schedule"]


def should_be_enabled(schedule, now):
    """Determine if guest WiFi should be enabled right now.

    Returns True if the current time falls within the on/off window
    for today's weekday. Returns False otherwise or if the day has
    no schedule entry.
    """
    day_name = DAY_NAMES[now.weekday()]
    day_schedule = schedule.get(day_name)

    if not day_schedule:
        return False

    on_time = datetime.strptime(day_schedule["on"], "%H:%M").time()
    off_time = datetime.strptime(day_schedule["off"], "%H:%M").time()
    current_time = now.time()

    return on_time <= current_time < off_time


def main():
    load_dotenv(SCRIPT_DIR / ".env")

    address = os.getenv("FRITZBOX_ADDRESS", "192.168.178.1")
    user = os.getenv("FRITZBOX_USER", "admin")
    password = os.getenv("FRITZBOX_PASSWORD")

    if not password:
        print(f"[{datetime.now()}] FEHLER: FRITZBOX_PASSWORD nicht gesetzt in .env")
        sys.exit(1)

    schedule = load_schedule()
    now = datetime.now()
    desired = should_be_enabled(schedule, now)

    try:
        guest_wlan = FritzGuestWLAN(address=address, user=user, password=password)
        current = guest_wlan.is_enabled

        if desired == current:
            status = "AN" if current else "AUS"
            print(f"[{now}] Gast-WLAN ist bereits {status} - keine Aenderung noetig")
        elif desired:
            guest_wlan.enable()
            print(f"[{now}] Gast-WLAN EINGESCHALTET")
        else:
            guest_wlan.disable()
            print(f"[{now}] Gast-WLAN AUSGESCHALTET")

    except Exception as e:
        print(f"[{now}] FEHLER bei Fritz!Box-Verbindung: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

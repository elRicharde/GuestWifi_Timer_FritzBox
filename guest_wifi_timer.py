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
from fritzconnection.core.exceptions import FritzAuthorizationError, FritzConnectionException
from fritzconnection.lib.fritzwlan import FritzGuestWLAN
from requests.exceptions import ConnectionError as RequestsConnectionError

SCRIPT_DIR = Path(__file__).resolve().parent
DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def timestamp(dt):
    """Format a datetime for log output."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def load_schedule():
    """Load the weekly schedule from schedule.yaml."""
    schedule_path = SCRIPT_DIR / "schedule.yaml"
    try:
        with open(schedule_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[{timestamp(datetime.now())}] FEHLER: {schedule_path} nicht gefunden")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[{timestamp(datetime.now())}] FEHLER: schedule.yaml ist keine gueltige YAML-Datei: {e}")
        sys.exit(1)

    if not isinstance(config, dict) or "schedule" not in config:
        print(f"[{timestamp(datetime.now())}] FEHLER: Schluessel 'schedule' fehlt in schedule.yaml")
        sys.exit(1)

    return config["schedule"]


def validate_schedule(schedule):
    """Validate schedule entries: check keys, time format, and on < off."""
    for day, times in schedule.items():
        if day not in DAY_NAMES:
            print(f"[{timestamp(datetime.now())}] FEHLER: Unbekannter Wochentag '{day}' in schedule.yaml")
            sys.exit(1)

        if "on" not in times or "off" not in times:
            print(f"[{timestamp(datetime.now())}] FEHLER: '{day}' braucht sowohl 'on' als auch 'off' in schedule.yaml")
            sys.exit(1)

        for key in ("on", "off"):
            try:
                datetime.strptime(times[key], "%H:%M")
            except ValueError:
                print(f"[{timestamp(datetime.now())}] FEHLER: Ungueltiges Zeitformat '{times[key]}' bei {day}.{key} (erwartet HH:MM)")
                sys.exit(1)

        on_time = datetime.strptime(times["on"], "%H:%M").time()
        off_time = datetime.strptime(times["off"], "%H:%M").time()
        if on_time >= off_time:
            print(f"[{timestamp(datetime.now())}] FEHLER: {day}.on ({times['on']}) muss vor {day}.off ({times['off']}) liegen (nachtuebergreifend nicht unterstuetzt)")
            sys.exit(1)


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
    now = datetime.now()
    load_dotenv(SCRIPT_DIR / ".env")

    address = os.getenv("FRITZBOX_ADDRESS", "192.168.178.1")
    user = os.getenv("FRITZBOX_USER", "admin")
    password = os.getenv("FRITZBOX_PASSWORD")

    if not password:
        print(f"[{timestamp(now)}] FEHLER: FRITZBOX_PASSWORD nicht gesetzt in .env")
        sys.exit(1)

    schedule = load_schedule()
    validate_schedule(schedule)
    desired = should_be_enabled(schedule, now)

    try:
        guest_wlan = FritzGuestWLAN(address=address, user=user, password=password)
        current = guest_wlan.is_enabled

        if desired == current:
            status = "AN" if current else "AUS"
            print(f"[{timestamp(now)}] Gast-WLAN ist bereits {status} - keine Aenderung noetig")
        elif desired:
            guest_wlan.enable()
            print(f"[{timestamp(now)}] Gast-WLAN EINGESCHALTET")
        else:
            guest_wlan.disable()
            print(f"[{timestamp(now)}] Gast-WLAN AUSGESCHALTET")

    except RequestsConnectionError:
        print(f"[{timestamp(now)}] FEHLER: Fritz!Box nicht erreichbar unter {address}")
        sys.exit(1)
    except FritzAuthorizationError:
        print(f"[{timestamp(now)}] FEHLER: Authentifizierung fehlgeschlagen - Zugangsdaten in .env pruefen")
        sys.exit(1)
    except FritzConnectionException as e:
        print(f"[{timestamp(now)}] FEHLER: Fritz!Box API-Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

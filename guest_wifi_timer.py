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


def parse_time(time_str):
    """Parse a HH:MM string into a time object."""
    return datetime.strptime(time_str, "%H:%M").time()


def get_windows(day_schedule):
    """Normalize a day's schedule to a list of {on, off} windows.

    Supports both single window (dict) and multiple windows (list).
    """
    if isinstance(day_schedule, dict):
        return [day_schedule]
    return day_schedule


def validate_schedule(schedule):
    """Validate schedule entries: check keys, time format, and on != off."""
    for day, entry in schedule.items():
        if day not in DAY_NAMES:
            print(f"[{timestamp(datetime.now())}] FEHLER: Unbekannter Wochentag '{day}' in schedule.yaml")
            sys.exit(1)

        windows = get_windows(entry)
        for i, times in enumerate(windows):
            label = f"{day}[{i}]" if len(windows) > 1 else day

            if "on" not in times or "off" not in times:
                print(f"[{timestamp(datetime.now())}] FEHLER: '{label}' braucht sowohl 'on' als auch 'off' in schedule.yaml")
                sys.exit(1)

            for key in ("on", "off"):
                try:
                    datetime.strptime(times[key], "%H:%M")
                except ValueError:
                    print(f"[{timestamp(datetime.now())}] FEHLER: Ungueltiges Zeitformat '{times[key]}' bei {label}.{key} (erwartet HH:MM)")
                    sys.exit(1)

            if times["on"] == times["off"]:
                print(f"[{timestamp(datetime.now())}] FEHLER: {label}.on und {label}.off duerfen nicht gleich sein")
                sys.exit(1)


def is_in_window(window, current_time):
    """Check if current_time falls within a single on/off window.

    Supports overnight windows where on > off.
    """
    on_time = parse_time(window["on"])
    off_time = parse_time(window["off"])

    if on_time < off_time:
        return on_time <= current_time < off_time
    else:
        return current_time >= on_time


def should_be_enabled(schedule, now):
    """Determine if guest WiFi should be enabled right now.

    Checks today's windows and yesterday's overnight windows.
    Supports multiple windows per day and overnight schedules.
    """
    current_time = now.time()

    # Check if yesterday's overnight windows extend into today
    yesterday_name = DAY_NAMES[(now.weekday() - 1) % 7]
    yesterday_entry = schedule.get(yesterday_name)
    if yesterday_entry:
        for window in get_windows(yesterday_entry):
            y_on = parse_time(window["on"])
            y_off = parse_time(window["off"])
            if y_on > y_off and current_time < y_off:
                return True

    # Check today's windows
    today_name = DAY_NAMES[now.weekday()]
    today_entry = schedule.get(today_name)
    if not today_entry:
        return False

    for window in get_windows(today_entry):
        if is_in_window(window, current_time):
            return True

    return False


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

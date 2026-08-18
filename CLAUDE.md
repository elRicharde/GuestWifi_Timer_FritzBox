# CLAUDE.md - GuestWifi Timer Fritz!Box

## Projekt-Überblick
Python-Script das auf einem Raspberry Pi per Cron-Job läuft und das Gast-WLAN einer Fritz!Box 7590 nach einem Wochenplan (schedule.yaml) automatisch ein-/ausschaltet. Kommunikation via TR-064 API mit der `fritzconnection`-Library.

## Hardware-Umgebung
- **Router**: Fritz!Box 7590 (Standard-IP: 192.168.178.1)
- **Raspberry Pi**: Läuft bereits mit Pi-hole (DNS-Adblocker), dieses Script wird zusätzlich auf dem selben Raspi deployed
- **Entwicklung**: Windows 11, Deployment auf Raspberry Pi (Linux/ARM)

## Design-Entscheidungen
Folgende Entscheidungen wurden bei der Projektplanung bewusst getroffen:
- **Python** statt Bash/Node.js → wegen `fritzconnection`-Library und guter Raspi-Unterstützung
- **YAML** für Zeitplan → gut lesbar, einfach editierbar (statt JSON oder hardcoded im Script)
- **.env-Datei** für Zugangsdaten → getrennt von Konfiguration, durch .gitignore geschützt
- **Cron-Job** statt Systemd-Service → einfacher, robuster, kein Daemon-Management nötig
- **Tageszeiten-basiert** (on/off pro Wochentag) → statt ganzer Tage ein/aus oder komplexerer Muster
- **Soll/Ist-Vergleich** → Script schaltet nur wenn nötig, vermeidet unnötige API-Calls bei jedem Cron-Lauf

## Architektur
- **Timer-Script** (`guest_wifi_timer.py`) - Cron-basiert, jede Minute, prüft Soll vs. Ist
- **Telegram Bot** (`telegram_bot.py`) - Daemon (systemd), erlaubt Override per Inline-Buttons
- **Override-Mechanismus** - Bot schreibt `override.json`, Timer-Script respektiert sie
- **Zielplattform**: Raspberry Pi (Linux/ARM) mit bestehendem Pi-hole, entwickelt auf Windows

## Projektstruktur
```
guest_wifi_timer.py   # Hauptscript (Einstiegspunkt, Cron-Job)
telegram_bot.py       # Telegram Bot fuer Override-Steuerung (systemd-Daemon)
schedule.yaml         # Wochenplan: on/off-Zeiten pro Wochentag (englische Namen)
logrotate.conf        # Log-Rotation (symlinked nach /etc/logrotate.d/)
override.json         # Temporaerer Override (von Bot geschrieben, NICHT im Git)
.env                  # Zugangsdaten + Bot-Token (NICHT im Git)
.env.example          # Vorlage für .env
requirements.txt      # Python-Abhängigkeiten
```

## Kommunikation
- Der Benutzer spricht Deutsch - alle Antworten, Erklärungen und Rückfragen auf Deutsch
- Commit-Messages und PR-Beschreibungen auf Englisch

## Wichtige Konventionen

### Sprache im Code
- **Code**: Englisch (Variablen, Funktionen, Docstrings)
- **Log-Ausgaben**: Deutsch (Benutzer-facing)
- **Konfiguration**: Englisch (YAML-Keys = englische Wochentage)
- **Dokumentation**: Deutsch (README, Kommentare wo nötig)

### Wochentage in schedule.yaml
Müssen englisch und lowercase sein: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`. Mapping über `datetime.weekday()` Index (0=Monday).

### Fritz!Box API
- Library: `fritzconnection` (High-Level-Klasse `FritzGuestWLAN`)
- Service: `WLANConfiguration3` = Gast-WLAN auf Fritz!Box 7590
- `guest_wlan.is_enabled` → aktueller Zustand (bool)
- `guest_wlan.enable()` / `guest_wlan.disable()` → Zustand ändern
- Braucht Fritz!Box-Benutzer mit Berechtigung "Fritz!Box Einstellungen"

### Zeitformat
- schedule.yaml verwendet `"HH:MM"` (24h, als String in Anführungszeichen)
- Logik: `on_time <= current_time < off_time` (on ist inklusiv, off ist exklusiv)
- Fehlt ein Wochentag im Zeitplan → Gast-WLAN bleibt an diesem Tag AUS

### Umgebungsvariablen (.env)
| Variable | Standard | Beschreibung |
|---|---|---|
| `FRITZBOX_ADDRESS` | `192.168.178.1` | IP der Fritz!Box |
| `FRITZBOX_USER` | `admin` | Benutzername |
| `FRITZBOX_PASSWORD` | *(pflicht)* | Passwort |
| `TELEGRAM_BOT_TOKEN` | *(pflicht fuer Bot)* | Token von @BotFather |
| `TELEGRAM_ALLOWED_USERS` | *(pflicht fuer Bot)* | Komma-getrennte Telegram User-IDs |

### Override-Mechanismus
- `telegram_bot.py` schreibt `override.json` mit Ablaufzeit
- `guest_wifi_timer.py` prüft bei jedem Lauf: Override vorhanden + nicht abgelaufen → WLAN bleibt AN
- Nach Ablauf löscht das Timer-Script die Datei automatisch
- Format: `{"until": "ISO-8601", "created": "ISO-8601"}`

### Logging
- Alle Ausgaben via `print()` nach stdout
- Format: `[{timestamp}] Nachricht`
- Cron leitet stdout/stderr in `timer.log` um

## Abhängigkeiten
- Python 3.7+
- `fritzconnection` - TR-064 API Client
- `python-dotenv` - .env-Datei laden
- `pyyaml` - YAML-Konfiguration parsen
- `python-telegram-bot` - Telegram Bot API (v21+, async)

## Sicherheit
- `.env` ist in `.gitignore` - niemals Zugangsdaten committen
- `FRITZBOX_PASSWORD` hat keinen Default - Script bricht ab wenn nicht gesetzt
- Keine Passwörter in Logs ausgeben

## Testen
Kein Test-Framework vorhanden. Manuell testen:
```bash
python3 guest_wifi_timer.py
```
Prüft den aktuellen Zeitplan und gibt den Soll/Ist-Vergleich auf stdout aus.

## Häufige Erweiterungen
- Logging in Datei statt stdout
- Statusabfrage als separates CLI-Kommando

## Fritz!Box TR-064 API Referenz
Für zukünftige Erweiterungen - weitere nützliche Services/Actions:
- `WLANConfiguration1` = 2.4 GHz WLAN, `WLANConfiguration2` = 5 GHz WLAN
- `GetInfo` Action → gibt Dict mit `NewSSID`, `NewEnable`, `NewStatus` ("Up"/"Disabled") zurück
- `SetEnable` Action → Parameter `NewEnable` (1=an, 0=aus)
- `FritzGuestWLAN.get_password()` → aktuelles Gast-WLAN-Passwort auslesen
- `FritzGuestWLAN.set_password("neues_pw")` → Passwort setzen
- CLI-Inspection: `fritzconnection -i <ip> -p <pw> -S WLANConfiguration3`

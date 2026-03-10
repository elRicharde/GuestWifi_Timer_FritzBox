# GuestWifi Timer - Fritz!Box 7590

Steuert das Gast-WLAN der Fritz!Box 7590 nach einem konfigurierbaren Wochenplan.
Läuft als Cron-Job auf einem Raspberry Pi.

## Setup auf dem Raspberry Pi

### 1. Repository klonen
```bash
git clone https://github.com/elRicharde/GuestWifi_Timer_FritzBox.git ~/guest_wifi_timer
cd ~/guest_wifi_timer
```
Für spätere Updates:
```bash
cd ~/guest_wifi_timer && git pull
```

### 2. Abhängigkeiten installieren
```bash
sudo apt update && sudo apt install python3-pip python3-venv -y
python3 -m venv ~/guest_wifi_timer/venv
source ~/guest_wifi_timer/venv/bin/activate
pip install -r requirements.txt
```

### 3. Zugangsdaten konfigurieren
```bash
cp .env.example .env
nano .env
```
Trage deine Fritz!Box-Zugangsdaten ein:
- `FRITZBOX_ADDRESS` - IP der Fritz!Box (Standard: 192.168.178.1)
- `FRITZBOX_USER` - Benutzername (muss in der Fritz!Box unter System > Fritz!Box-Benutzer existieren)
- `FRITZBOX_PASSWORD` - Passwort

**Wichtig:** Der Benutzer braucht die Berechtigung "Fritz!Box Einstellungen" in der Fritz!Box-Benutzerverwaltung.

### 4. Zeitplan anpassen
```bash
nano ~/guest_wifi_timer/schedule.yaml
```
Passe die Ein/Aus-Zeiten pro Wochentag an (24h-Format, Anführungszeichen beibehalten):
```yaml
schedule:
  # Wochentage: on/off im 24h-Format
  # Nachtuebergreifend moeglich: off < on bedeutet "aus am naechsten Tag"
  # Mehrere Zeitfenster pro Tag moeglich (als Liste mit -)
  monday:
    on: "06:00"
    off: "22:00"
  tuesday:
    on: "06:00"
    off: "22:00"
  wednesday:
    # Beispiel: mehrere Fenster (Mittagspause)
    - on: "06:00"
      off: "12:00"
    - on: "14:00"
      off: "22:00"
  thursday:
    on: "06:00"
    off: "22:00"
  friday:
    on: "06:00"
    off: "02:00"    # aus: Samstag 02:00
  saturday:
    on: "06:00"
    off: "02:00"    # aus: Sonntag 02:00
  sunday:
    on: "06:00"
    off: "22:00"
```
- Tage die fehlen = Gast-WLAN bleibt an diesem Tag **aus**
- `off` < `on` = nachtübergreifend (z.B. `off: "02:00"` = aus am nächsten Tag um 02:00)
- Mehrere Fenster pro Tag: Liste mit `-` verwenden (siehe Mittwoch-Beispiel)

### 5. Manuell testen
```bash
~/guest_wifi_timer/venv/bin/python ~/guest_wifi_timer/guest_wifi_timer.py
```

### 6. Cron-Job einrichten
```bash
crontab -e
```
Folgende Zeile hinzufügen (prüft jede Minute):
```
* * * * * ~/guest_wifi_timer/venv/bin/python ~/guest_wifi_timer/guest_wifi_timer.py >> ~/guest_wifi_timer/timer.log 2>&1
```

### 7. Log-Rotation einrichten (optional)
Das Log wächst mit der Zeit. Einfache Lösung mit logrotate:
```bash
sudo nano /etc/logrotate.d/guest-wifi-timer
```
Folgenden Inhalt einfügen:
```
~/guest_wifi_timer/timer.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

## Dateien

| Datei | Beschreibung |
|---|---|
| `guest_wifi_timer.py` | Hauptscript - prüft Zeitplan und schaltet Gast-WLAN |
| `schedule.yaml` | Wochenplan mit Ein/Aus-Zeiten |
| `.env` | Fritz!Box-Zugangsdaten (nicht im Git) |
| `.env.example` | Vorlage für .env |
| `requirements.txt` | Python-Abhängigkeiten |

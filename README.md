# GuestWifi Timer - Fritz!Box 7590

Steuert das Gast-WLAN der Fritz!Box 7590 nach einem konfigurierbaren Wochenplan.
Läuft als Cron-Job auf einem Raspberry Pi.

## Setup auf dem Raspberry Pi

### 1. Code auf den Raspberry Pi bringen

**Option A: Per SCP vom PC kopieren** (einfachster Weg, kein SSH-Key auf dem Raspi nötig)

Vom Windows-PC aus (PowerShell):
```powershell
scp -r .\GuestWifi_Timer_FritzBox pi@<raspi-ip>:~/guest_wifi_timer
```
Für spätere Updates nach Code-Änderungen:
```powershell
scp .\guest_wifi_timer.py .\schedule.yaml .\requirements.txt pi@<raspi-ip>:~/guest_wifi_timer/
```

**Option B: Git Clone mit Deploy Key** (ermöglicht `git pull` direkt auf dem Raspi)

1. SSH-Key auf dem Raspi erzeugen:
```bash
ssh-keygen -t ed25519 -C "raspi-deploy-key" -f ~/.ssh/github_deploy
```
2. Public Key anzeigen und kopieren:
```bash
cat ~/.ssh/github_deploy.pub
```
3. In GitHub unter *Repository → Settings → Deploy keys → Add deploy key* einfügen (Read-only reicht)
4. SSH-Config auf dem Raspi anlegen:
```bash
nano ~/.ssh/config
```
Folgenden Inhalt einfügen:
```
Host github.com
    IdentityFile ~/.ssh/github_deploy
```
5. Klonen:
```bash
git clone git@github.com:elRicharde/GuestWifi_Timer_FritzBox.git ~/guest_wifi_timer
```
Für spätere Updates:
```bash
cd ~/guest_wifi_timer && git pull
```

Dann auf dem Raspi:
```bash
cd ~/guest_wifi_timer
```

### 2. Abhängigkeiten installieren
```bash
pip3 install -r requirements.txt
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
Bearbeite `schedule.yaml` mit deinen gewünschten Ein/Aus-Zeiten pro Wochentag:
```yaml
schedule:
  monday:
    on: "08:00"
    off: "22:00"
  # ...
```

### 5. Manuell testen
```bash
python3 ~/guest_wifi_timer/guest_wifi_timer.py
```

### 6. Cron-Job einrichten
```bash
crontab -e
```
Folgende Zeile hinzufügen (prüft jede Minute):
```
* * * * * /usr/bin/python3 /home/pi/guest_wifi_timer/guest_wifi_timer.py >> /home/pi/guest_wifi_timer/timer.log 2>&1
```

### 7. Log-Rotation einrichten (optional)
Das Log wächst mit der Zeit. Einfache Lösung mit logrotate:
```bash
sudo nano /etc/logrotate.d/guest-wifi-timer
```
Folgenden Inhalt einfügen:
```
/home/pi/guest_wifi_timer/timer.log {
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

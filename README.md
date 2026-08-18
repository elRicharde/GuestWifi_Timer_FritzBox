# GuestWifi Timer - Fritz!Box 7590

Steuert das Gast-WLAN der Fritz!Box 7590 automatisch nach Wochenplan.
Optional: Per Telegram-Bot das WLAN spontan verlaengern (z.B. wenn Gaeste laenger bleiben).

**Laeuft auf einem Raspberry Pi** — braucht nur Strom und Netzwerk, kein Monitor.

---

## Was macht das Projekt?

1. **Timer-Script** (`guest_wifi_timer.py`) — laeuft jede Minute per Cron-Job, schaut in den Wochenplan (`schedule.yaml`) und schaltet das Gast-WLAN ein oder aus
2. **Telegram Bot** (`telegram_bot.py`) — optional, laeuft dauerhaft im Hintergrund. Damit kannst du per Handy das WLAN spontan verlaengern, auch wenn es laut Zeitplan schon aus waere

---

## Voraussetzungen

- Ein **Raspberry Pi** im selben Netzwerk wie die Fritz!Box (z.B. der Pi-hole-Raspi)
- **SSH-Zugang** zum Raspberry Pi (z.B. via PuTTY oder Terminal)
- Eine **Fritz!Box 7590** (andere Modelle mit Gast-WLAN funktionieren vermutlich auch)
- Fuer den Telegram Bot: ein Smartphone mit **Telegram**

---

## Teil 1: Fritz!Box vorbereiten

Bevor das Script die Fritz!Box steuern kann, braucht es einen Benutzer mit den richtigen Rechten.

### 1.1 Fritz!Box-Benutzer anlegen (oder pruefen)

1. Im Browser `http://fritz.box` oeffnen und einloggen
2. Gehe zu **System > Fritz!Box-Benutzer**
3. Entweder einen bestehenden Benutzer verwenden oder einen neuen anlegen
4. Wichtig: Der Benutzer braucht die Berechtigung **"Fritz!Box Einstellungen"** — ohne diese kann das Script das WLAN nicht schalten
5. Benutzername und Passwort merken — die brauchst du gleich

---

## Teil 2: Timer auf dem Raspberry Pi einrichten

Ab hier arbeitest du auf dem Raspberry Pi (per SSH verbinden).

### 2.1 Repository herunterladen

```bash
git clone https://github.com/elRicharde/GuestWifi_Timer_FritzBox.git ~/guest_wifi_timer
```

> Das laedt alle Dateien in den Ordner `~/guest_wifi_timer` auf deinem Pi.

Fuer spaetere Updates:
```bash
cd ~/guest_wifi_timer && git pull
```

### 2.2 Python-Umgebung einrichten

```bash
sudo apt update && sudo apt install python3-pip python3-venv -y
```

> Installiert die noetige Software fuer Python. Falls schon vorhanden, passiert nichts Schlimmes.

```bash
python3 -m venv ~/guest_wifi_timer/venv
```

> Erstellt eine eigene Python-Umgebung im Projektordner. So kommen sich die Pakete nicht mit anderen Programmen auf dem Pi in die Quere.

```bash
source ~/guest_wifi_timer/venv/bin/activate
pip install -r ~/guest_wifi_timer/requirements.txt
```

> Aktiviert die Umgebung und installiert alle benoetigten Pakete.

### 2.3 Zugangsdaten eintragen

```bash
cd ~/guest_wifi_timer
cp .env.example .env
nano .env
```

> Erstellt eine Kopie der Vorlage und oeffnet sie zum Bearbeiten.

Aendere die Werte auf deine Fritz!Box-Daten:

```
FRITZBOX_ADDRESS=192.168.178.1
FRITZBOX_USER=admin
FRITZBOX_PASSWORD=dein_echtes_passwort
```

| Variable | Was eintragen? |
|---|---|
| `FRITZBOX_ADDRESS` | IP deiner Fritz!Box. Standard ist `192.168.178.1` — nur aendern wenn du das umgestellt hast |
| `FRITZBOX_USER` | Der Benutzername aus Schritt 1.1 |
| `FRITZBOX_PASSWORD` | Das Passwort aus Schritt 1.1 |

Speichern: `Ctrl+O`, Enter, `Ctrl+X`

### 2.4 Zeitplan anpassen

```bash
nano ~/guest_wifi_timer/schedule.yaml
```

Hier legst du fest, wann das Gast-WLAN an und aus sein soll:

```yaml
schedule:
  monday:
    on: "06:00"
    off: "22:00"
  tuesday:
    on: "06:00"
    off: "22:00"
  wednesday:
    on: "06:00"
    off: "22:00"
  thursday:
    on: "06:00"
    off: "22:00"
  friday:
    on: "06:00"
    off: "02:00"    # aus: Samstag 02:00 (naechster Tag)
  saturday:
    on: "06:00"
    off: "02:00"    # aus: Sonntag 02:00 (naechster Tag)
  sunday:
    on: "06:00"
    off: "22:00"
```

**Regeln:**
- Zeiten im **24-Stunden-Format** mit Anfuehrungszeichen: `"06:00"`, `"22:00"`
- Wochentage auf **Englisch**: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`
- Ein Tag der **fehlt** = Gast-WLAN bleibt an diesem Tag **aus**
- `off` kleiner als `on` = nachtuebergreifend (z.B. `off: "02:00"` bedeutet: aus am naechsten Tag um 2 Uhr)

**Mehrere Zeitfenster an einem Tag** (z.B. Mittagspause):
```yaml
  wednesday:
    - on: "06:00"
      off: "12:00"
    - on: "14:00"
      off: "22:00"
```

Speichern: `Ctrl+O`, Enter, `Ctrl+X`

### 2.5 Testen ob alles funktioniert

```bash
~/guest_wifi_timer/venv/bin/python ~/guest_wifi_timer/guest_wifi_timer.py
```

Du solltest eine Ausgabe wie diese sehen:
```
[2026-05-14 20:15:00] Gast-WLAN ist bereits AN - keine Aenderung noetig
```

Wenn du eine Fehlermeldung bekommst:
- `Fritz!Box nicht erreichbar` — Stimmt die IP in der `.env`?
- `Authentifizierung fehlgeschlagen` — Stimmen Benutzername und Passwort?
- `FRITZBOX_PASSWORD nicht gesetzt` — Hast du die `.env`-Datei gespeichert?

### 2.6 Cron-Job einrichten (automatischer Timer)

```bash
crontab -e
```

> Oeffnet die Cron-Konfiguration. Beim ersten Mal wirst du nach einem Editor gefragt — waehle `nano` (Nummer 1).

Fuege ganz unten diese Zeile ein:

```
* * * * * ~/guest_wifi_timer/venv/bin/python ~/guest_wifi_timer/guest_wifi_timer.py >> ~/guest_wifi_timer/timer.log 2>&1
```

> Das bedeutet: Fuehre das Script **jede Minute** aus und schreibe die Ausgabe in `timer.log`.

Speichern: `Ctrl+O`, Enter, `Ctrl+X`

**Fertig!** Der Timer laeuft jetzt automatisch. Du kannst das Log pruefen mit:
```bash
tail -20 ~/guest_wifi_timer/timer.log
```

### 2.7 Log-Rotation einrichten

Das Log waechst mit der Zeit (~3,5 MB/Monat). Damit es nicht die SD-Karte vollschreibt, ist eine `logrotate.conf` im Repo enthalten. Einmalig verlinken:

```bash
sudo ln -sf ~/guest_wifi_timer/logrotate.conf /etc/logrotate.d/guest-wifi-timer
```

> Haelt maximal 4 Wochen Log-Dateien und komprimiert aeltere. Aenderungen im Repo greifen automatisch beim naechsten Rotationslauf.

**Hinweis:** Der Pfad in `logrotate.conf` ist auf `/home/richarde/guest_wifi_timer/` eingestellt. Falls dein Benutzer anders heisst, passe den Pfad in der Datei an.

---

## Teil 3: Telegram Bot einrichten (optional)

Mit dem Telegram Bot kannst du das Gast-WLAN per Handy spontan verlaengern.
Zum Beispiel: Es ist 22:05, das WLAN ist laut Zeitplan aus, aber dein Gast braucht noch Internet — du drueckst "+2h" und das WLAN bleibt bis 00:05 an.

### 3.1 Telegram Bot erstellen

Das passiert auf deinem **Handy** in der Telegram-App:

1. Oeffne Telegram und suche nach **@BotFather** (das ist der offizielle Bot zum Erstellen von Bots)
2. Schreibe ihm `/newbot`
3. Er fragt nach einem **Namen** — z.B. `Gast-WLAN Timer`
4. Er fragt nach einem **Benutzernamen** — muss auf `bot` enden, z.B. `mein_gastwlan_bot`
5. BotFather antwortet mit einem **Token** — das sieht so aus: `7123456789:AAF1x2y3z4...`
6. **Kopiere dieses Token** — das brauchst du gleich

### 3.2 Deine Telegram User-ID herausfinden

Damit nur **du** den Bot steuern kannst (und nicht irgendwer der den Bot findet):

1. Suche in Telegram nach **@userinfobot**
2. Schreibe ihm irgendwas (z.B. "hi")
3. Er antwortet mit deiner **User-ID** — eine Zahl wie `123456789`
4. **Merke dir diese Zahl**

> Willst du mehrere Personen berechtigen? Dann brauch jeder seine ID von @userinfobot.

### 3.3 Bot-Zugangsdaten auf dem Raspi eintragen

Zurueck auf dem **Raspberry Pi** (per SSH):

```bash
nano ~/guest_wifi_timer/.env
```

Fuege am Ende diese zwei Zeilen hinzu:

```
TELEGRAM_BOT_TOKEN=7123456789:AAF1x2y3z4_dein_echtes_token_hier
TELEGRAM_ALLOWED_USERS=123456789
```

| Variable | Was eintragen? |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Das Token von BotFather aus Schritt 3.1 |
| `TELEGRAM_ALLOWED_USERS` | Deine User-ID aus Schritt 3.2. Mehrere IDs mit Komma trennen: `123456789,987654321` |

Speichern: `Ctrl+O`, Enter, `Ctrl+X`

### 3.4 Bot als Hintergrund-Service einrichten

Der Bot muss dauerhaft laufen (nicht nur einmal wie der Timer). Dafuer richten wir einen systemd-Service ein:

```bash
sudo nano /etc/systemd/system/guest-wifi-bot.service
```

Folgenden Inhalt einfuegen:

```ini
[Unit]
Description=Guest WiFi Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/guest_wifi_timer
ExecStart=/home/pi/guest_wifi_timer/venv/bin/python /home/pi/guest_wifi_timer/telegram_bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> **Hinweis:** Falls dein Benutzer nicht `pi` heisst, aendere `User=pi` und die Pfade `/home/pi/...` entsprechend.

Speichern: `Ctrl+O`, Enter, `Ctrl+X`

Jetzt den Service aktivieren und starten:

```bash
sudo systemctl daemon-reload
sudo systemctl enable guest-wifi-bot
sudo systemctl start guest-wifi-bot
```

> `enable` = startet automatisch nach jedem Neustart des Pi
> `start` = startet den Bot jetzt sofort

### 3.5 Pruefen ob der Bot laeuft

```bash
sudo systemctl status guest-wifi-bot
```

Du solltest `active (running)` sehen. Falls nicht:
```bash
sudo journalctl -u guest-wifi-bot -n 20
```
> Zeigt die letzten 20 Log-Zeilen — hilfreich bei Fehlern.

### 3.6 Bot testen

1. Oeffne Telegram auf dem Handy
2. Suche nach dem Bot-Namen den du in Schritt 3.1 vergeben hast
3. Schreibe `/start`
4. Es erscheinen **Buttons**: +0,5h, +1h, +1,5h ... bis +5h
5. Druecke z.B. **+2h** — das WLAN bleibt jetzt 2 Stunden ueber den Zeitplan hinaus an
6. Mit **"Override aufheben"** kannst du den Override vorzeitig beenden

### Bot-Befehle

| Befehl | Was passiert? |
|---|---|
| `/start` | Zeigt die Override-Buttons und den aktuellen Status |
| `/status` | Zeigt nur den aktuellen Override-Status |

---

## Wie funktioniert der Override?

1. Du drueckst im Telegram Bot "+2h"
2. Der Bot schreibt eine Datei `override.json` mit dem Ablaufzeitpunkt
3. Beim naechsten Cron-Lauf (innerhalb von 60 Sekunden) liest das Timer-Script diese Datei
4. Solange der Override aktiv ist, bleibt das WLAN **an** — egal was im Zeitplan steht
5. Nach Ablauf loescht das Timer-Script die Datei automatisch und der normale Zeitplan gilt wieder

---

## Dateien

| Datei | Beschreibung |
|---|---|
| `guest_wifi_timer.py` | Hauptscript — prueft Zeitplan + Override und schaltet Gast-WLAN |
| `telegram_bot.py` | Telegram Bot — Override per Inline-Buttons |
| `schedule.yaml` | Wochenplan: wann soll das WLAN an/aus sein |
| `override.json` | Temporaerer Override (wird automatisch erstellt und geloescht) |
| `.env` | Deine Zugangsdaten + Bot-Token (nicht im Git, nie teilen!) |
| `.env.example` | Vorlage fuer die `.env`-Datei |
| `requirements.txt` | Liste der Python-Pakete |

---

## Updates installieren

```bash
cd ~/guest_wifi_timer
git pull
source venv/bin/activate
pip install -r requirements.txt
```

Falls sich am Bot etwas geaendert hat:
```bash
sudo systemctl restart guest-wifi-bot
```

Der Timer (Cron-Job) braucht keinen Neustart — er verwendet beim naechsten Lauf automatisch den neuen Code.

---

## Troubleshooting

| Problem | Loesung |
|---|---|
| `Fritz!Box nicht erreichbar` | Stimmt die IP in `.env`? Ist der Pi im selben Netzwerk? |
| `Authentifizierung fehlgeschlagen` | Benutzername/Passwort in `.env` pruefen. Hat der User die Berechtigung "Fritz!Box Einstellungen"? |
| Bot antwortet nicht | `sudo systemctl status guest-wifi-bot` pruefen. Token richtig kopiert? |
| Bot sagt "Nicht autorisiert" | Deine Telegram User-ID stimmt nicht mit `TELEGRAM_ALLOWED_USERS` ueberein |
| WLAN schaltet trotz Override aus | Laeuft der Cron-Job? `tail -5 ~/guest_wifi_timer/timer.log` pruefen |
| Override wird ignoriert | Steht die `override.json` im richtigen Ordner (`~/guest_wifi_timer/`)? |

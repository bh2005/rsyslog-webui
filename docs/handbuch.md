# RSYSLOG Manager PWA — Benutzerhandbuch

**Ihre Organisation · IT-Infrastruktur**  
Version 1.0 · Stand: Mai 2026

---

## Inhaltsverzeichnis

1. [Übersicht](#1-übersicht)
2. [Anmeldung und Rollen](#2-anmeldung-und-rollen)
3. [Dashboard](#3-dashboard)
4. [Konfiguration](#4-konfiguration)
5. [Log-Viewer](#5-log-viewer)
6. [Benutzerkonten](#6-benutzerkonten)
7. [Installation & Deployment](#7-installation--deployment)
8. [Konfiguration der Anwendung](#8-konfiguration-der-anwendung)
9. [API-Referenz](#9-api-referenz)
10. [Häufige Fragen](#10-häufige-fragen)

---

## 1. Übersicht

RSYSLOG Manager PWA ist ein webbasiertes Verwaltungs-Frontend für den rsyslog-Dienst auf Debian-basierten Linux-Servern. Es ermöglicht Administratoren und Operatoren, den Dienst zu überwachen, die Konfiguration zu bearbeiten und Logs direkt im Browser einzusehen — ohne direkte SSH-Verbindung.

Die Anwendung ist als **Progressive Web App (PWA)** umgesetzt und kann auf Desktop und Mobilgeräten installiert werden.

### Funktionsübersicht

| Funktion | Beschreibung |
|---|---|
| Dashboard | Dienststatus, Version, Uptime auf einen Blick |
| Konfiguration | rsyslog.conf anzeigen, bearbeiten und mit Backup speichern |
| Dienst-Reload | Konfiguration live neu laden ohne Neustart |
| Log-Viewer | Aktuelle journalctl-Logs direkt im Browser |
| Rollensystem | Admin / Operator / Viewer mit abgestuften Rechten |
| PWA-Support | Installierbar auf Desktop und Mobilgeräten |

### Unterstützte Systeme

- Debian 11 (Bullseye), 12 (Bookworm), 13 (Trixie)
- Ubuntu 20.04, 22.04, 24.04
- Alle Systeme mit rsyslog und systemd

---

## 2. Anmeldung und Rollen

### Anmeldung

1. Rufen Sie die Anwendung im Browser auf (URL vom Administrator erfragen).
2. Geben Sie Benutzername und Passwort ein.
3. Klicken Sie auf **Anmelden**.

Nach erfolgreicher Anmeldung werden Sie automatisch zum Dashboard weitergeleitet. Die Sitzung bleibt aktiv bis zum Ablauf des Tokens (Standard: 1 Stunde) oder bis zum manuellen Abmelden.

**Standard-Zugangsdaten (müssen nach Ersteinrichtung geändert werden):**

| Benutzer | Passwort | Rolle |
|---|---|---|
| `admin` | `admin123` | Admin |
| `operator` | `operator123` | Operator |
| `viewer` | `viewer123` | Viewer |

> **Wichtig:** Die Standard-Passwörter müssen vor dem Produktiveinsatz über die Umgebungsvariablen `ADMIN_PASSWORD` geändert werden. Operator- und Viewer-Passwörter werden über das `.env`-File konfiguriert.

### Rollen und Berechtigungen

| Berechtigung | Admin | Operator | Viewer |
|---|:---:|:---:|:---:|
| Dashboard ansehen | ✓ | ✓ | ✓ |
| Dienststatus abrufen | ✓ | ✓ | ✓ |
| Konfiguration lesen | ✓ | ✓ | ✓ |
| Logs lesen | ✓ | ✓ | ✓ |
| Konfiguration bearbeiten | ✓ | ✓ | — |
| Dienst neu laden (reload) | ✓ | ✓ | — |
| Admin-Bereich | ✓ | — | — |

**Rollenbeschreibungen:**

- **Admin** — Voller Zugriff auf alle Funktionen, einschließlich administrativer Bereiche. Empfohlen für IT-Administratoren.
- **Operator** — Kann Konfiguration bearbeiten und den Dienst neu laden, hat aber keinen Zugriff auf administrative Funktionen. Geeignet für Betriebspersonal.
- **Viewer** — Nur Lesezugriff. Kann Status, Konfiguration und Logs einsehen, aber nichts ändern. Geeignet für Monitoring oder Audits.

### Sitzungs-Ende

Die Sitzung endet automatisch nach Ablauf des JWT-Tokens (Standard: 60 Minuten) oder wenn Sie **Abmelden** klicken. Bei Ablauf werden Sie automatisch zur Anmeldeseite weitergeleitet.

---

## 3. Dashboard

Das Dashboard ist die Startseite nach der Anmeldung und bietet einen sofortigen Überblick über den rsyslog-Dienst.

### Kopfzeile

Rechts oben wird angezeigt:
- **Benutzername** und **Rolle** der angemeldeten Person
- Rollenbeschreibung:
  - Admin → „Voller Zugriff"
  - Operator → „Konfiguration & Reload"
  - Viewer → „Nur Anzeige"

### Dienst-Karte (Service Management)

| Anzeige | Bedeutung |
|---|---|
| **Status** | `active` (grün) oder `inactive` / `failed` (rot/grau) |
| **Version** | Installierte rsyslog-Versionsnummer |
| **Uptime** | Zeitpunkt seit dem letzten Start des Dienstes |
| **Reload-Schaltfläche** | Lädt die Konfiguration neu (nur Admin/Operator sichtbar) |

> Der Reload sendet `systemctl reload rsyslog` — der Dienst bleibt aktiv, die Konfiguration wird neu eingelesen.

### Konfigurations-Karte

| Anzeige | Bedeutung |
|---|---|
| **Pfad** | Pfad zur aktiven Konfigurationsdatei (`/etc/rsyslog.conf`) |
| **Zusammenfassung** | Erste Zeile der Konfigurationsdatei |
| **Zuletzt geändert** | Zeitstempel der letzten Dateiänderung |
| **Bearbeitbar** | `Ja` / `Nein` je nach Rolle |
| **Link** | Direktlink zur Konfigurationsseite |

### Log-Analyse-Karte

Direktlink zur Log-Viewer-Seite mit einem kurzen Hinweis auf die verfügbaren Funktionen.

### Admin-Karte

Nur für Benutzer mit der Rolle **Admin** sichtbar. Enthält administrative Hinweise und Schnellzugriffe.

---

## 4. Konfiguration

*(Admin und Operator)*

Die Konfigurationsseite zeigt den vollständigen Inhalt der Datei `/etc/rsyslog.conf` und ermöglicht die direkte Bearbeitung im Browser.

### Seite öffnen

Navigieren Sie zu **Konfiguration** in der oberen Navigationsleiste.

### Konfigurations-Editor

- Der Textbereich zeigt den aktuellen Inhalt der `rsyslog.conf`.
- **Admin und Operator** können den Text direkt bearbeiten.
- **Viewer** sehen den Inhalt als schreibgeschützten Text; ein Hinweis erklärt die fehlende Berechtigung.

Über dem Editor werden angezeigt:
- **Konfigurationsdatei:** Pfad der aktiven Datei
- **Zuletzt geändert:** Datum und Uhrzeit der letzten Änderung

### Konfiguration speichern

1. Nehmen Sie die gewünschten Änderungen im Textbereich vor.
2. Klicken Sie **Konfiguration speichern**.
3. Vor dem Speichern wird automatisch ein Backup der aktuellen Konfiguration angelegt.
4. Eine Bestätigung erscheint bei Erfolg.

> **Hinweis:** Das Speichern allein aktiviert die neue Konfiguration noch nicht. Der Dienst muss anschließend neu geladen werden.

### Dienst neu laden

Klicken Sie **Dienst neu laden** (Reload), um rsyslog anzuweisen, die neue Konfiguration einzulesen. Der Dienst bleibt dabei aktiv — es handelt sich um keinen Neustart.

> **Empfehlung:** Validieren Sie die Konfiguration vor dem Reload mit `rsyslogd -N1` auf dem Server, um Syntaxfehler zu vermeiden. Eine integrierte Syntaxprüfung ist in Planung.

### Backup-Verhalten

Beim Speichern wird die bisherige Konfiguration automatisch gesichert (Dateiname: `rsyslog.conf.bak_<Zeitstempel>`). Damit ist ein manuelles Zurücksetzen möglich, falls die neue Konfiguration Probleme verursacht.

---

## 5. Log-Viewer

*(Alle Rollen)*

Der Log-Viewer zeigt die aktuellen rsyslog-Journal-Einträge, abgerufen via `journalctl -u rsyslog`.

### Seite öffnen

Navigieren Sie zu **Logs** in der oberen Navigationsleiste.

### Anzahl der Zeilen

Im Eingabefeld **Zeilenanzahl** können Sie festlegen, wie viele Log-Zeilen angezeigt werden:
- Minimum: 10 Zeilen
- Maximum: 1000 Zeilen
- Standard: 100 Zeilen

### Aktualisieren

Klicken Sie **Aktualisieren**, um die Logs neu zu laden. Die Anzeige wird nicht automatisch aktualisiert (kein Live-Streaming).

### Ausgabe-Format

Die Ausgabe entspricht dem `journalctl`-Standardformat:
```
Mai 18 10:23:45 hostname rsyslogd[1234]: message text
```

---

## 6. Benutzerkonten

### Benutzer-Verwaltung

RSYSLOG Manager verwendet ein **In-Memory-Benutzerverzeichnis** — Benutzer werden nicht in einer Datenbank gespeichert, sondern beim Start der Anwendung aus der Konfiguration geladen.

**Aktuelle Benutzer:**

| Benutzername | Konfiguriert über | Standardwert |
|---|---|---|
| `admin` | `ADMIN_USERNAME` / `ADMIN_PASSWORD` | admin / admin123 |
| `operator` | `OPERATOR_PASSWORD` in `.env` | operator123 |
| `viewer` | `VIEWER_PASSWORD` in `.env` | viewer123 |

### Passwörter ändern

Passwörter werden über Umgebungsvariablen in der `.env`-Datei gesetzt:

```bash
# backend/.env
JWT_SECRET=ihr-sicherer-schlüssel-min-32-zeichen
ADMIN_USERNAME=admin
ADMIN_PASSWORD=IhrSicheresAdminPasswort
OPERATOR_PASSWORD=IhrOperatorPasswort
VIEWER_PASSWORD=IhrViewerPasswort
```

Nach Änderung der `.env`-Datei muss der Backend-Dienst neu gestartet werden:

```bash
# Docker
docker compose restart api

# systemd
sudo systemctl restart rsyslog-manager-api
```

> **Wichtig:** Benutzersitzungen werden bei einem Neustart nicht explizit invalidiert, da JWT-Token stateless sind. Bereits ausgestellte Token bleiben bis zum Ablauf (`JWT_EXPIRATION_SECONDS`) gültig.

### Passwörter in der Produktion

Verwenden Sie in der Produktion ausschließlich starke, zufällige Passwörter:

```bash
# Sicheres Passwort generieren
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

---

## 7. Installation & Deployment

### Voraussetzungen

| Komponente | Mindestversion |
|---|---|
| Docker Engine | 24.0+ |
| Docker Compose | v2.20+ |
| Ziel-OS | Debian 11+ / Ubuntu 20.04+ |
| rsyslog | Muss auf dem Host installiert sein |
| systemd | Für `systemctl`/`journalctl`-Integration |

> **Wichtig:** Das Backend muss auf dem Server laufen, auf dem rsyslog installiert ist und `systemctl reload rsyslog` ausgeführt werden darf. Für Remote-Verwaltung mehrerer Server ist eine SSH/API-Erweiterung geplant.

### Schnellstart mit Docker Compose

```bash
git clone <repo-url> rsyslog-manager-pwa
cd rsyslog-manager-pwa

# Konfiguration anlegen
cp backend/.env.example backend/.env
# .env anpassen: JWT_SECRET setzen (PFLICHT!), Passwörter ändern
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Starten
docker compose up -d --build
```

Die Anwendung ist dann unter `http://<server-ip>` erreichbar (via Caddy-Proxy).

### Produktiv-Deployment mit HTTPS (Caddy)

Die mitgelieferte `Caddyfile` konfiguriert automatisch HTTPS via Let's Encrypt:

```caddy
rsyslog-manager.example.com {
    reverse_proxy /api/* api:8000
    reverse_proxy /* web:80
    encode gzip
}
```

**Schritte:**
1. DNS-Eintrag für Ihre Domain auf die Server-IP zeigen lassen.
2. In der `Caddyfile` den Hostnamen anpassen.
3. `docker compose up -d --build` ausführen.
4. Caddy holt automatisch ein Let's Encrypt-Zertifikat.

### Produktiv-Deployment mit Nginx + systemd

Für Umgebungen ohne Docker:

#### Backend (systemd-Service)

```bash
# Abhängigkeiten installieren
cd /opt/rsyslog-manager-pwa/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Systemd-Service erstellen
sudo tee /etc/systemd/system/rsyslog-manager-api.service <<'EOF'
[Unit]
Description=RSYSLOG Manager API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/rsyslog-manager-pwa/backend
EnvironmentFile=/opt/rsyslog-manager-pwa/backend/.env
ExecStart=/opt/rsyslog-manager-pwa/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now rsyslog-manager-api
```

#### Frontend (Nginx + statische Dateien)

```bash
# Frontend bauen
cd /opt/rsyslog-manager-pwa
npm install && npm run build

# Nginx-Konfiguration
sudo tee /etc/nginx/sites-available/rsyslog-manager <<'EOF'
server {
    listen 80;
    server_name rsyslog-manager.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name rsyslog-manager.example.com;

    ssl_certificate     /etc/letsencrypt/live/rsyslog-manager.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rsyslog-manager.example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;

    # API
    location /api/ {
        proxy_pass         http://127.0.0.1:8000/;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
    }

    # SPA (Vue Router)
    location / {
        root   /opt/rsyslog-manager-pwa/dist;
        try_files $uri $uri/ /index.html;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/rsyslog-manager /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### systemctl-Berechtigungen

Das Backend ruft `systemctl reload rsyslog` und `systemctl show rsyslog` auf. Der Prozess-Benutzer benötigt dafür entweder Root-Rechte oder eine sudoers-Ausnahme:

```bash
# sudoers-Eintrag (empfohlen für Produktion)
sudo tee /etc/sudoers.d/rsyslog-manager <<'EOF'
rsyslog-manager ALL=(ALL) NOPASSWD: /bin/systemctl reload rsyslog, /bin/systemctl show rsyslog, /bin/systemctl is-active rsyslog, /bin/systemctl is-enabled rsyslog
EOF
```

---

## 8. Konfiguration der Anwendung

Alle Einstellungen werden über Umgebungsvariablen in `backend/.env` gesetzt.

### Umgebungsvariablen

| Variable | Pflicht | Standard | Beschreibung |
|---|---|---|---|
| `JWT_SECRET` | **Ja** | `CHANGE_ME` | Signaturschlüssel für JWT-Token (min. 32 Zeichen, zufällig) |
| `ADMIN_USERNAME` | Nein | `admin` | Benutzername des Admins |
| `ADMIN_PASSWORD` | **Ja** | `admin123` | Admin-Passwort — in Produktion immer ändern! |
| `OPERATOR_PASSWORD` | Nein | `operator123` | Passwort für den Operator-Account |
| `VIEWER_PASSWORD` | Nein | `viewer123` | Passwort für den Viewer-Account |
| `JWT_EXPIRATION_SECONDS` | Nein | `3600` | Token-Gültigkeit in Sekunden (Standard: 1 Stunde) |

### JWT_SECRET generieren

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### `.env`-Beispieldatei

```bash
# backend/.env
JWT_SECRET=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
ADMIN_USERNAME=admin
ADMIN_PASSWORD=MeinSicheresAdminPasswort!2026
OPERATOR_PASSWORD=OperatorPass!123
VIEWER_PASSWORD=ViewerPass!456
JWT_EXPIRATION_SECONDS=3600
```

### Token-Ablauf-Verhalten

| Einstellung | Auswirkung |
|---|---|
| `3600` (1h) | Standard — Sitzung nach 1 Stunde abgelaufen |
| `28800` (8h) | Für Schichtbetrieb sinnvoll |
| `86400` (24h) | Für Monitoring-Displays ohne häufige Anmeldung |

---

## 9. API-Referenz

Basis-URL: `/api` (Produktion) oder `http://localhost:8000` (Entwicklung)

### Authentifizierung

Alle Endpunkte außer `/api/auth/login` und `/api/health` erfordern einen gültigen JWT-Token im `Authorization`-Header:

```http
Authorization: Bearer <jwt-token>
```

### Authentifizierungs-Endpunkte

#### `POST /api/auth/login`

Anmelden und JWT-Token erhalten.

**Request:**
```json
{
  "username": "admin",
  "password": "meinPasswort"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_at": "2026-05-18T11:00:00Z",
  "role": "admin"
}
```

**Fehler:**
- `401` — Ungültige Zugangsdaten

---

#### `GET /api/auth/me`

Informationen zum aktuell angemeldeten Benutzer.

**Response (200):**
```json
{
  "username": "admin",
  "role": "admin"
}
```

---

### rsyslog-Endpunkte

#### `GET /api/rsyslog/status`

Aktueller Dienststatus.

**Response (200):**
```json
{
  "service": "rsyslog",
  "status": "active",
  "enabled": true,
  "version": "8.2312.0",
  "uptime": "2026-05-15T02:00:00Z"
}
```

---

#### `GET /api/rsyslog/config`

Aktueller Konfigurationsinhalt.

**Response (200):**
```json
{
  "config_path": "/etc/rsyslog.conf",
  "content": "# /etc/rsyslog.conf ...",
  "last_modified": "2026-05-10T14:30:00Z",
  "summary": "# /etc/rsyslog.conf -- default configuration ...",
  "editable": true
}
```

---

#### `PUT /api/rsyslog/config`

Konfiguration speichern (Backup wird automatisch angelegt).

**Erforderliche Rolle:** Admin oder Operator

**Request:**
```json
{
  "content": "# Neue rsyslog.conf\n$ModLoad imuxsock\n..."
}
```

**Response (200):**
```json
{
  "ok": true,
  "backup_path": "/etc/rsyslog.conf.bak_20260518_143022"
}
```

---

#### `POST /api/rsyslog/reload`

Konfiguration ohne Dienstunterbrechung neu laden (`systemctl reload rsyslog`).

**Erforderliche Rolle:** Admin oder Operator

**Response (200):**
```json
{
  "ok": true,
  "message": "rsyslog erfolgreich neu geladen"
}
```

**Fehler:**
- `500` — systemctl reload fehlgeschlagen (Details im `message`-Feld)

---

#### `GET /api/rsyslog/logs?lines=100`

Aktuelle Journal-Logs des rsyslog-Dienstes.

**Query-Parameter:**

| Parameter | Standard | Beschreibung |
|---|---|---|
| `lines` | `100` | Anzahl zurückzugebender Zeilen (10–1000) |

**Response (200):**
```json
{
  "logs": "Mai 18 10:23:45 srv01 rsyslogd[1234]: [origin ...]\nMai 18 10:23:46 ..."
}
```

---

#### `GET /api/health`

Health-Check (kein Token erforderlich).

**Response (200):**
```json
{
  "status": "ok"
}
```

---

## 10. Häufige Fragen

**Q: Nach dem Login erscheint sofort wieder die Anmeldeseite.**  
A: Das JWT_SECRET in der `.env` ist möglicherweise leer oder auf den Standardwert gesetzt, der beim Start eine Warnung erzeugt. Setzen Sie einen gültigen `JWT_SECRET`-Wert und starten Sie den Backend-Dienst neu.

**Q: „Dienst neu laden" schlägt mit 500 fehl.**  
A: Der Backend-Prozess hat keine ausreichenden Rechte für `systemctl reload rsyslog`. Richten Sie eine sudoers-Ausnahme ein (siehe [Abschnitt 7 — systemctl-Berechtigungen](#systemctl-berechtigungen)) oder führen Sie den Dienst als Root aus (nicht empfohlen).

**Q: Der Operator kann die Konfiguration nicht speichern, obwohl er angemeldet ist.**  
A: Prüfen Sie, ob der Token noch gültig ist (max. `JWT_EXPIRATION_SECONDS`). Melden Sie sich ab und wieder an. Prüfen Sie außerdem, ob die Rolle im Token korrekt ist (`GET /api/auth/me`).

**Q: Wie lange ist eine Sitzung gültig?**  
A: Standardmäßig 3600 Sekunden (1 Stunde). Einstellbar über `JWT_EXPIRATION_SECONDS` in der `.env`-Datei.

**Q: Kann ich mehrere rsyslog-Server verwalten?**  
A: Derzeit unterstützt die Anwendung nur den Server, auf dem das Backend läuft. Multi-Host-Verwaltung via SSH/API ist als P1-Feature geplant (siehe `openpoints.md`).

**Q: Wo werden Konfigurations-Backups gespeichert?**  
A: Im selben Verzeichnis wie die Konfigurationsdatei (`/etc/rsyslog.conf.bak_<Zeitstempel>`). Der Benutzer, unter dem das Backend läuft, muss Schreibrechte in `/etc/` besitzen.

**Q: Die PWA lässt sich nicht auf dem Smartphone installieren.**  
A: Die PWA-Installation erfordert HTTPS. Stellen Sie sicher, dass die Anwendung über eine sichere Verbindung erreichbar ist (Caddy oder Nginx mit SSL-Zertifikat, siehe Abschnitt 7).

**Q: Der Log-Viewer zeigt keine Logs an.**  
A: Prüfen Sie, ob `journalctl -u rsyslog` auf dem Server Ausgaben liefert. Der Backend-Prozess benötigt Lesezugriff auf das systemd-Journal (`journald`-Gruppe oder Root-Rechte).

**Q: Wie ändere ich die Anzahl der Standard-Log-Zeilen?**  
A: Im Log-Viewer direkt über das Eingabefeld **Zeilenanzahl**. Ein persistenter Standardwert ist aktuell nicht konfigurierbar.

**Q: Ist eine Zwei-Faktor-Authentifizierung geplant?**  
A: 2FA ist als optionales Feature im Backlog gelistet. Bis dahin empfehlen wir starke Passwörter und Netzwerkzugriffsbeschränkungen (Firewall, VPN).

---

## Entwicklung (Quick Reference)

### Lokale Entwicklungsumgebung

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\Activate.ps1         # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env               # JWT_SECRET setzen
uvicorn app.main:app --reload --port 8000

# Frontend (separates Terminal)
npm install
npm run dev                        # http://localhost:5173
```

Die Vite-Dev-Config proxyt `/api/*` automatisch auf `http://localhost:8000`.

### Docker-Entwicklung (Hot-Reload)

```bash
docker compose up --build
# Frontend:  http://localhost:5173  (Vite HMR)
# Backend:   http://localhost:8000  (uvicorn --reload)
# Caddy:     http://localhost       (Proxy)
```

### Build für Produktion

```bash
npm run build        # Erzeugt frontend/dist/
docker compose -f docker-compose.yml up -d --build
```

---

*Dieses Handbuch gilt für RSYSLOG Manager PWA v1.0.*  
*Support: IT-Infrastruktur Ihre Organisation*

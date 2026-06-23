# RSYSLOG Manager PWA — Open Points

## Ziel

Eine Progressive Web App für das Management eines RSYSLOG Servers auf Debian 13.
Das Frontend wird über HTTPS auf Port 443 erreichbar sein.

## Wichtige Punkte (P1)

### 1. Service-Management
- [x] `rsyslog`-Status anzeigen (aktiv, gestoppt, Fehler)
- [x] Starten / Stoppen / Neustarten des Dienstes (`POST /rsyslog/start|stop|restart`, Admin only)
- [x] Auto-Recovery-Prüfung und Systemd-Status (NRestarts, SubState, PID, ExecStatus im Dashboard)

### 2. Konfigurationsverwaltung
- [x] Anzeige und Bearbeitung von `rsyslog.conf`
- [x] Support für inkludierte Konfigurationsdateien (`/etc/rsyslog.d/` — Tab im Config-Editor, Anzeigen/Editieren/Löschen, managed-Schutz)
- [x] Syntax-Prüfung vor Reload (`rsyslogd -N1` — Button im Config-Editor und Include-Editor, Ergebnis farbig inline)
- [x] Versionshistorie / Rollback für Konfigurationsänderungen (Snapshots, Diff-Ansicht, 1-Klick-Restore im Config-Editor)

### 3. Log-Analyse
- [x] Live-Log-Ansicht und Aktualisierung (Remote-Logs + journalctl, Aktualisieren-Button)
- [x] Filter nach Facility, Severity, Host, Programm
- [x] Suche in Logs (Freitext-Suche mit Highlight)
- [x] Warnungen / Fehler im Log-Stream hervorheben (farbige Zeilenmarkierung + Severity-Badges)

### 4. Remote-Host-Management
- [x] Verwaltung mehrerer Debian-Hosts (Host-CRUD in Einstellungen: Name, IP, Anzeigename)
- [x] Host-basierte Zugriffssteuerung (User ↔ Host-Zuweisung für Logs und Alerts)
- [x] Log-Archivierung pro Host (`/data/syslog/HOSTNAME/YYYY/MM/`, logrotate konfigurierbar)
- [ ] SSH/API-Pairing der Hosts (direkter SSH-Zugriff auf Remote-Hosts via paramiko — Endpoint-Gerüst vorhanden)
- [ ] Host-Inventar mit Systemstatus (CPU/RAM/Uptime der Remote-Hosts)
- [x] Backup / Restore der Konfiguration (Download-Button + Upload/Restore im Config-Editor)

### 5. Sicherheit & Zugriff (höchste Priorität)
- [x] Authentifizierung und Rollen (Admin / Operator / Viewer, JWT)
- [x] Feingranulare Zugriffssteuerung: Menü, Actions, Hosts, Konfiguration
- [x] Host-basierte Zugriffssteuerung: User sieht/erhält Alerts nur von zugewiesenen Hosts
- [x] Mehrere Berechtigungsstufen: Admin, Operator, Viewer
- [x] Sicherer Betrieb über HTTPS (Caddy Reverse-Proxy, Port 8453 lokal / 443 produktiv)
- [x] E-Mail-Alerts mit granularer User/Host-Filterung (ommail, `/etc/rsyslog.d/99-email-alerts.conf`)
- [x] Audit-Log für Änderungen an Konfiguration, Hosts, Benutzern und Dienst-Aktionen
- [ ] Zugangskontrolle für Remote-Hosts (SSH-Key-Management)

## Empfohlene Punkte (P2)

### 6. PWA / Offline-Funktionalität
- [x] Installierbare App (Service Worker + Manifest, PWA)
- [ ] Offline-Fallback für Host-Übersicht und Audit-Informationen
- [ ] Netzwerkstatus und Reconnect-Hinweise
- [ ] Push-Benachrichtigungen für kritische Zustände

### 7. Monitoring & Alerts
- [x] Health-Check rsyslog-Dienst (Status, Uptime, Version im Dashboard)
- [x] E-Mail-Alerts für kritische Log-Ereignisse (ommail, konfigurierbar nach Severity und Host)
- [x] Statistik-Dashboard (CPU, RAM, Disk /, Disk /data/syslog, Events/sec — Auto-Refresh 10s, Gauge-Balken, Severity-Farben)
- [x] Integration mit Check_MK (`GET /api/checkmk` — Local-Check-Format, Script-Snippet, Live-Vorschau im UI)
- [x] Prometheus (`GET /api/metrics` — text/plain Scrape-Endpoint, scrape_config-Snippet im UI)

### 8. Benutzerfreundlichkeit
- [x] Responsive Design (Desktop-optimiert)
- [x] Schnellaktionen im Dashboard (Reload, Restart, Status)
- [ ] Konfigurations-Assistent für typische Debian/rsyslog-Setups

## Optionale Verbesserungen (P3)

- [x] Templates für Debian-`rsyslog.conf` (rsyslog-Template-Snippet in Einstellungen)
- [ ] Zentralisierte Verwaltung mehrerer rsyslog-Server
- [ ] Automatische Best-Practice-Prüfungen
- [ ] Lokales Log-Caching für Offline-Diagnose

---

## Offene Prioritäten (nächste Schritte)

| Prio | Punkt | Aufwand |
|------|-------|---------|
| P2 | SSH/API-Pairing Remote-Hosts | Groß |
| P3 | Konfigurations-Assistent für Debian/rsyslog-Setups | Mittel |

---

*Zuletzt aktualisiert: 2026-06-11*

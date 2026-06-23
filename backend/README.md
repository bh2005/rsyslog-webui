# RSYSLOG Manager API

Dieses Backend liefert eine minimale Authentifizierungs-API für das RSYSLOG Manager PWA-Projekt.

## Installation

```bash
cd rsyslog-manager-pwa/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Start

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

Builden und starten mit Docker:

```bash
docker build -t rsyslog-manager-api .
```

Oder per Compose aus dem Projektstamm:

```bash
docker compose up --build api
```

## Konfiguration

Kopiere `.env.example` nach `.env` und passe `JWT_SECRET`, `ADMIN_USERNAME` und `ADMIN_PASSWORD` an.

## Endpunkte

- `POST /auth/login` — Login mit Benutzername und Passwort
- `GET /auth/me` — aktueller Nutzer
- `GET /health` — Health-Check

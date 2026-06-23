# RSYSLOG Manager

A web-based management UI for rsyslog servers — built with Vue 3 + TypeScript (Vite) and a FastAPI backend.

## Features

- **Dashboard** — rsyslog service status, configuration overview
- **Log Viewer** — live log streaming, search, filter by host / severity / facility
- **Receiver Management** — manage syslog receivers and their configuration
- **Configuration Editor** — edit rsyslog config with backup and reload
- **Service Control** — start, stop, restart, reload rsyslog
- **RBAC** — roles: `admin`, `operator`, `viewer`
- **JWT Authentication** — secure session handling
- **PWA** — installable as a Progressive Web App (offline-capable dashboard)

## Architecture

```
┌──────────────────────────────────────────────┐
│  Docker Container                            │
│                                              │
│  ┌────────────────┐   ┌──────────────────┐   │
│  │  FastAPI       │   │  Vue 3 + Vite    │   │
│  │  (uvicorn)     │◄──│  TypeScript      │   │
│  │  Port 8080     │   │  PWA / Tailwind  │   │
│  └────────┬───────┘   └──────────────────┘   │
│           │                                  │
│  ┌────────▼───────┐                          │
│  │  rsyslog       │                          │
│  │  (host socket  │                          │
│  │   / SSH)       │                          │
│  └────────────────┘                          │
└──────────────────────────────────────────────┘
```

| Component | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, python-jose, passlib |
| Frontend | Vue 3, TypeScript, Vite, Tailwind CSS |
| Auth | JWT (local users) |
| Deployment | Docker / docker-compose |

## Quick Start

### Prerequisites

- Docker >= 24
- docker-compose >= 2.x
- rsyslog running on the target host

### Start

```bash
git clone https://github.com/bh2005/rsyslog-webui.git
cd rsyslog-webui
cp .env.example .env   # set SECRET_KEY
docker compose up -d
```

App available at **http://\<server\>:8080**

Default login: `admin` / `admin` — **change immediately!**

### Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key — required |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` (default: `INFO`) |

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Frontend
npm install
npm run dev   # Vite dev server on :5173
```

## License

MIT — see [LICENSE](LICENSE)

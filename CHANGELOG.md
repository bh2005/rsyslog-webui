# Changelog

## [Unreleased]

### Added
- Log analysis: time range filter (presets 1h / 6h / 24h / 7d or custom from/to)
- `GET /rsyslog/remote-logs` accepts optional `since` / `until` (ISO 8601); filtering happens
  server-side so the row limit does not cut off older ranges

### Changed
- Receiver: sender hosts without any log file show "keine Logs empfangen" instead of an empty cell
- Help panel: corrected log analysis limits (10-2000), added time range, new help page for the receiver view
- Manual: log analysis (remote syslog) section and `remote-logs` API entry

## [0.1.0] - 2026-05-18

### Added
- Backend JWT authentication with `/auth/login` and `/auth/me` endpoints
- Role-based access control for `admin`, `operator`, and `viewer`
- Frontend login flow with persisted token and auto session restore
- Dashboard overview for rsyslog service status, configuration metadata, and role details
- `GET /rsyslog/config` endpoint with editable flag based on role
- `PUT /rsyslog/config` endpoint for saving rsyslog configuration with backup
- `POST /rsyslog/reload` endpoint for reloading rsyslog configuration
- `GET /rsyslog/logs` endpoint to view recent rsyslog journal logs
- Frontend pages for configuration editing and log viewing
- Navigation links for dashboard, configuration, and logs
- Improved README and project documentation
- Added Dockerfiles and docker-compose setup for frontend and backend

### Changed
- Updated routing and authenticated navigation in frontend
- Added config edit permissions for admin/operator
- Added backend service integration with Debian `systemctl` and `journalctl`

# Changelog

## [Unreleased]

### Added
- Log analysis: save, update, rename, delete and reload up to 5 filters per user (stored server-side in
  `saved_filters.json`; `GET/PUT /users/me/filters`, `PATCH/DELETE /users/me/filters/{id}`)
- Log analysis: optional regex search (`regex=true`); evaluated with the `regex` package and a per-line
  timeout so a pathological pattern cannot block the API; invalid/too complex patterns return `400`
- Audit log: logins, logouts and failed logins (`auth.login`, `auth.logout`, `auth.login_failed`) with client IP; new `POST /auth/logout`
- Log analysis: time range filter (presets 1h / 6h / 24h / 7d or custom from/to)
- Log analysis: multi-select for severity and facility; dark mode colors for the log table
- `GET /rsyslog/remote-logs` accepts optional `since` / `until` (ISO 8601) plus `severity`, `facility`, `program`, `q`; filtering happens
  server-side so the row limit does not cut off older ranges

### Fixed
- Reading large log files no longer loads them completely into memory (streaming tail), which could get the API process killed
  by the OOM killer
- Receiver: the directory lookup is case-insensitive, so the misleading "create directory" button no longer appears for existing folders
- Validation errors from custom validators returned HTTP 500 instead of 422 (non-serializable error context)
- API errors now also carry `detail` (as the frontend expects). Before, the UI always showed its generic
  fallback (e.g. "Login failed") instead of the backend message (e.g. locked account, invalid regex)
- Dark mode: table row hover and audit log colors were unreadable (hard-coded light colors)
- Log analysis: with host "alle" the first file filled the row limit, so filters (e.g. facility `kern`) showed no entries.
  All filters now run server-side before the limit and entries of all hosts are merged by time;
  log files are read from the end instead of fully (large files)

### Changed
- Performance: routes that do blocking file/process I/O are now plain `def` handlers (run in a thread pool) instead of
  `async def`, so one heavy request no longer blocks the whole worker; the thread pool is limited (`WORKER_THREADS`, default 8)
  to keep small hosts responsive
- Statistics: the events-per-second counter only reads the bytes appended since the last call (and skips files that were not
  touched for an hour) instead of re-reading every log file on each request
- Event rate: timestamps are extracted with a regex (works for lines that are not valid JSON) and the time zone offset is
  respected; cache TTL reduced to 30 s
- Host names are handled case-insensitively (rsyslog keeps the capitalization of the sender); assigned hosts are compared lowercased
- Heartbeat: works for both the host-based and the category-based log layout; empty group folders are listed per subfolder
  (e.g. `bigip/node1`, `bigip/node2`) so it is visible which group is silent; response contains `unrestricted`
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

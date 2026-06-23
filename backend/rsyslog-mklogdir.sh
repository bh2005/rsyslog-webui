#!/bin/bash
# /usr/local/bin/rsyslog-mklogdir
# Legt ein Log-Verzeichnis unter /data/syslog/<host>/ an und setzt
# korrekte Eigentuemerschaft (syslog:adm, chmod 755).
# Wird via sudo von rsyslog-mgr aufgerufen (siehe /etc/sudoers.d/rsyslog-mgr).

set -euo pipefail

HOST="${1:-}"
if [[ -z "$HOST" ]]; then
    echo "Usage: rsyslog-mklogdir <hostname>" >&2
    exit 1
fi

# Nur sichere Zeichen erlauben (Hostname oder IP)
if [[ ! "$HOST" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]{0,62}$ ]]; then
    echo "Ungültiger Hostname: $HOST" >&2
    exit 1
fi

TARGET="/data/syslog/$HOST"

mkdir -p "$TARGET"
chown rsyslog-mgr:adm "$TARGET"
chmod 755 "$TARGET"

echo "OK: $TARGET (rsyslog-mgr:adm 755)"

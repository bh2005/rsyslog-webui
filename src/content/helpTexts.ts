export const helpTexts: Record<string, string> = {

  '/': `
<h2>Dashboard</h2>
<p>Zeigt den aktuellen Status des rsyslog-Dienstes auf einen Blick.</p>
<h3>Status-Karten</h3>
<ul>
  <li><b>Service-Status</b> – running / stopped / failed</li>
  <li><b>Uptime</b> – Zeit seit letztem Start</li>
  <li><b>Editierbar</b> – ob rsyslog.conf beschreibbar ist</li>
  <li><b>Rolle</b> – Deine aktuelle Berechtigungsstufe</li>
</ul>
<h3>Systemd-Details</h3>
<ul>
  <li><b>SubState</b> – Fein-Status (running, exited, dead …)</li>
  <li><b>PID</b> – Prozess-ID des Hauptprozesses</li>
  <li><b>Neustarts</b> – Zählt Auto-Restarts. Rot = Dienst hatte Probleme!</li>
  <li><b>Exit-Status</b> – Letzter Exit-Code. 0 = OK</li>
</ul>
<h3>Aktionen</h3>
<p><b>Konfiguration neu laden</b> schickt SIGHUP an rsyslog (kein Neustart, keine Unterbrechung). Nur für Operator und Admin.</p>
<hr>
<p class="help-tip">💡 Erhöhter Neustarts-Zähler deutet auf einen Konfigurationsfehler oder Ressourcenproblem hin. Syntax-Check in der Konfiguration ausführen.</p>
`,

  '/my-hosts': `
<h2>Meine Hosts</h2>
<p>Persönliches Dashboard mit allen Hosts, für die Du berechtigt bist.</p>
<h3>Host-Karte</h3>
<ul>
  <li><b>Farbiger Rand</b> – Grün OK, Gelb &gt;15 min, Rot &gt;1h kein Log</li>
  <li><b>Letzter Eingang</b> – Zeitstempel des zuletzt empfangenen Logs</li>
  <li><b>24h-Sparkline</b> – Mini-Histogramm der letzten 24 Stunden</li>
  <li><b>Anomalie-Tag</b> – Erscheint wenn aktuelle Rate &gt;3× Durchschnitt</li>
</ul>
<h3>Heartbeat-Status</h3>
<table>
  <tr><th>Status</th><th>Bedeutung</th></tr>
  <tr><td>✅ OK</td><td>Logs in letzten 15 Minuten empfangen</td></tr>
  <tr><td>⚠ Warnung</td><td>Letzter Log 15–60 Minuten her</td></tr>
  <tr><td>🔴 Kritisch</td><td>Kein Log seit über 1 Stunde</td></tr>
  <tr><td>❓ Unbekannt</td><td>Kein Log-Verzeichnis vorhanden</td></tr>
</table>
<hr>
<p class="help-tip">💡 Auto-Refresh alle 30s aktiv. Wartungsmodus-Banner erscheint wenn Alerts pausiert sind.</p>
`,

  '/config': `
<h2>Konfiguration</h2>
<p>Bearbeiten von <code>/etc/rsyslog.conf</code> und Include-Dateien.</p>
<h3>Tabs</h3>
<ul>
  <li><b>rsyslog.conf</b> – Hauptkonfiguration. Download- und Restore-Buttons in der Toolbar.</li>
  <li><b>/etc/rsyslog.d/</b> – Alle .conf-Dateien im Include-Verzeichnis. <span style="background:#f1f5f9;padding:1px 5px;border-radius:3px;font-size:11px;">managed</span>-Dateien können nicht manuell gelöscht werden.</li>
  <li><b>Historie</b> – Automatische Snapshots bei jedem Speichern (max. 10). Diff-Ansicht und 1-Klick-Rollback.</li>
</ul>
<h3>Syntax-Prüfung</h3>
<p>Führt <code>rsyslogd -N1</code> gegen die aktuelle Editor-Version aus – <b>ohne</b> die Datei zu überschreiben. Ergebnis erscheint grün/rot direkt über dem Editor.</p>
<h3>Rollback</h3>
<p>Im Tab <b>Historie</b> Snapshot auswählen → <b>Wiederherstellen</b>. Wechselt danach automatisch zur rsyslog.conf-Ansicht. Dienst danach manuell neu laden!</p>
<h3>Backup / Restore</h3>
<ul>
  <li><b>↓ Download</b> – Aktuelle rsyslog.conf herunterladen (Zeitstempel im Dateinamen)</li>
  <li><b>↑ Restore</b> – .conf-Datei hochladen und wiederherstellen (max. 512 KB)</li>
</ul>
<hr>
<p class="help-tip">💡 Immer Syntax prüfen bevor speichern! Ein Fehler in rsyslog.conf kann den Dienst zum Absturz bringen.</p>
`,

  '/logs': `
<h2>Log-Analyse</h2>
<p>Live-Ansicht der empfangenen Syslog-Einträge von Remote-Hosts.</p>
<h3>Filter</h3>
<ul>
  <li><b>Host</b> – Server-seitiger Filter (nur sichtbare Hosts)</li>
  <li><b>Severity</b> – 0 Emerg bis 7 Debug</li>
  <li><b>Facility</b> – kern, user, mail, daemon, auth …</li>
  <li><b>Programm</b> – Freitext-Filter auf programname</li>
  <li><b>Suche</b> – Volltext in msg-Feld, Treffer werden <mark>gelb markiert</mark></li>
  <li><b>Limit</b> – Maximale Anzahl Einträge (100–5000)</li>
</ul>
<h3>Farb-Kodierung</h3>
<table>
  <tr><th>Farbe</th><th>Severity</th></tr>
  <tr><td style="background:#fef2f2">Rot</td><td>emerg, alert, crit</td></tr>
  <tr><td style="background:#fff7ed">Orange</td><td>err</td></tr>
  <tr><td style="background:#fefce8">Gelb</td><td>warning</td></tr>
  <tr><td>Weiß</td><td>notice, info, debug</td></tr>
</table>
<hr>
<p class="help-tip">💡 Nur Hosts sichtbar, für die Du berechtigt bist. Admins sehen alle.</p>
`,

  '/logfiles': `
<h2>Log-Dateien</h2>
<p>Datei-Explorer für archivierte Log-Dateien auf dem Server.</p>
<h3>Verzeichnisstruktur</h3>
<pre style="background:#f8fafc;padding:8px;border-radius:4px;font-size:11px;">/data/syslog/
  └─ HOSTNAME/
      └─ YYYY/
          └─ MM/
              └─ HOSTNAME_[IP].log</pre>
<h3>Navigation</h3>
<p>Klick auf Host → Jahr → Monat öffnet die Dateiliste. Datei anklicken zeigt Größe, Änderungsdatum und den Download-Button.</p>
<h3>Download</h3>
<p>Nur Dateien von berechtigten Hosts können heruntergeladen werden. Pfad-Traversal wird serverseitig verhindert.</p>
<hr>
<p class="help-tip">💡 Für die Analyse einzelner Einträge die <b>Log-Ansicht</b> verwenden. Der Datei-Explorer ist für den Download ganzer Archiv-Dateien gedacht.</p>
`,

  '/stats': `
<h2>Monitoring & Statistik</h2>
<p>System-Ressourcen, Host-Heartbeat, Event-Rate und Integrations-Endpunkte.</p>
<h3>Metriken-Karten</h3>
<ul>
  <li><b>CPU</b> – Prozent-Auslastung + Load 1/5/15 min</li>
  <li><b>RAM</b> – Verbrauch in MB / % (aus /proc/meminfo)</li>
  <li><b>Disk /</b> – Root-Dateisystem</li>
  <li><b>Disk /data/syslog</b> – Log-Partition (UNKNOWN wenn nicht gemountet)</li>
  <li><b>Events/sec</b> – Geschätzte Rate aus Logfile-Delta</li>
</ul>
<h3>Host-Heartbeat</h3>
<p>Tabelle mit letztem Log-Eingang pro Host. Grün &lt;15min, Gelb &lt;1h, Rot &gt;1h.</p>
<h3>Event-Rate Histogram</h3>
<p>Balkendiagramm pro Host. Zwischen <b>24h (stündlich)</b> und <b>14 Tage (täglich)</b> umschalten. Ein <span style="background:#fecaca;padding:1px 4px;border-radius:2px;font-size:11px;">roter Balken</span> zeigt eine Anomalie (aktuelle Rate &gt;3× Durchschnitt) an.</p>
<h3>Integrations</h3>
<ul>
  <li><b>Prometheus</b> – <code>GET /api/metrics</code> im text/plain Scrape-Format</li>
  <li><b>Check_MK</b> – <code>GET /api/checkmk</code> im Local-Check-Format</li>
</ul>
<hr>
<p class="help-tip">💡 Auto-Refresh alle 10s. Anomalie-Emails werden nur verschickt wenn E-Mail in den Einstellungen konfiguriert ist und kein Wartungsfenster aktiv ist.</p>
`,

  '/users': `
<h2>Benutzerverwaltung</h2>
<p>Anlegen, Bearbeiten und Löschen von Benutzern. Nur für Admins.</p>
<h3>Rollen</h3>
<table>
  <tr><th>Rolle</th><th>Rechte</th></tr>
  <tr><td><b>admin</b></td><td>Alles, inkl. Benutzer und Einstellungen verwalten</td></tr>
  <tr><td><b>operator</b></td><td>Logs, Konfiguration lesen/schreiben, Dienst steuern</td></tr>
  <tr><td><b>viewer</b></td><td>Nur lesen – Logs, Status, Monitoring</td></tr>
</table>
<h3>Host-Zuweisung</h3>
<p><b>Leer</b> = Benutzer sieht alle Hosts (kein Filter).<br>
<b>Mit Hosts</b> = Benutzer sieht nur Logs und bekommt Alerts von diesen Hosts.</p>
<h3>E-Mail-Adresse</h3>
<p>Wird für Anomalie-Alerts und rsyslog-ommail-Regeln verwendet. Nur wirksam wenn E-Mail in den Einstellungen aktiviert ist.</p>
<hr>
<p class="help-tip">💡 Den eigenen Admin-Account kann man nicht löschen oder degradieren. Passwort ändern über den Klick auf den eigenen Benutzernamen unten links.</p>
`,

  '/groups': `
<h2>Gruppen</h2>
<p>Gruppen fassen mehrere Benutzer zusammen und ermöglichen gemeinsame Host-Zuweisung.</p>
<h3>Konzept</h3>
<ul>
  <li>Eine Gruppe hat <b>Mitglieder</b> (Benutzer) und <b>Hosts</b></li>
  <li>Benutzer erhalten Zugriff auf Hosts aus <b>direkt zugewiesenen Hosts</b> + <b>Gruppen-Hosts</b></li>
  <li>Leere Gruppen-Host-Liste = Gruppe schränkt nicht ein</li>
</ul>
<h3>Anwendungsbeispiel</h3>
<pre style="background:#f8fafc;padding:8px;border-radius:4px;font-size:11px;">Gruppe "Linux-Team"
  Mitglieder: alice, bob
  Hosts: linux-srv01, linux-srv02

→ alice + bob sehen Logs von linux-srv01 + linux-srv02
→ E-Mail-Alerts für diese Hosts gehen an alice + bob</pre>
<h3>Alert-Empfänger</h3>
<p>Anomalie-Emails gehen an alle Benutzer (mit E-Mail-Adresse), die einen Host direkt oder via Gruppe zugewiesen haben. Unrestricted-Benutzer erhalten alle Alerts.</p>
<hr>
<p class="help-tip">💡 Nach Gruppen-Änderungen in den Einstellungen <b>"E-Mail-Konfiguration neu generieren"</b> ausführen um die ommail-Regeln zu aktualisieren.</p>
`,

  '/settings': `
<h2>Einstellungen</h2>
<h3>Hosts verwalten</h3>
<p>Definiert die bekannten Remote-Hosts. Name = Hostname wie er in den Logs erscheint. Wird für Host-Zuweisung und Zugriffssteuerung verwendet.</p>
<h3>Log-Archivierung & Rotation</h3>
<p>Generiert <code>/etc/logrotate.d/rsyslog-remote</code>. Das rsyslog-Template-Snippet zeigt den passenden rsyslog.conf-Abschnitt für das <code>HOSTNAME/YYYY/MM/</code>-Verzeichnisschema.</p>
<h3>Log-Weiterleitung</h3>
<p>Schreibt <code>/etc/rsyslog.d/99-forwarding.conf</code>. TCP (<code>@@</code>) oder UDP (<code>@</code>). Leer lassen = keine Weiterleitung.</p>
<h3>E-Mail-Alerts</h3>
<p>SMTP-Einstellungen für rsyslog ommail. Empfänger werden automatisch aus den Benutzer- und Gruppen-Zuweisungen abgeleitet. Nach Änderungen <b>E-Mail-Konfiguration neu generieren</b> klicken.</p>
<h3>Wartungsfenster</h3>
<ul>
  <li><b>Manuelle Pause</b> – Alerts für X Stunden pausieren (z.B. während Reboot)</li>
  <li><b>Zeitfenster</b> – Wiederkehrende Fenster (z.B. Mo–Fr 22:00–06:00)</li>
</ul>
<hr>
<p class="help-tip">💡 Managed-Dateien (forwarding, email-alerts) werden vom System automatisch überschrieben. Nicht manuell editieren.</p>
`,

  '/audit': `
<h2>Audit-Log</h2>
<p>Unveränderliches Protokoll aller Aktionen im System. Nur für Admins lesbar.</p>
<h3>Protokollierte Aktionen</h3>
<table>
  <tr><th>Kategorie</th><th>Aktionen</th></tr>
  <tr><td>config.*</td><td>Konfiguration gespeichert, Rollback, Restore</td></tr>
  <tr><td>service.*</td><td>Reload, Start, Stop, Restart</td></tr>
  <tr><td>user.*</td><td>Anlegen, Bearbeiten, Löschen, Passwort-Änderung</td></tr>
  <tr><td>group.*</td><td>Anlegen, Bearbeiten, Löschen</td></tr>
  <tr><td>settings.*</td><td>Hosts, Forwarding, Email, Rotation, Wartung</td></tr>
  <tr><td>anomaly.*</td><td>Anomalie-Alert versendet</td></tr>
</table>
<h3>Filter</h3>
<p>Client-seitig: nach Benutzer, Aktions-Typ, Detail-Text filterbar.</p>
<h3>Log leeren</h3>
<p>Löscht alle Einträge (nur Admin). Die Aktion selbst wird vorher noch eingetragen.</p>
<hr>
<p class="help-tip">💡 Das Audit-Log liegt unter <code>/etc/rsyslog-manager/audit.log</code> als JSON-Lines und kann auch direkt auf dem Server gelesen werden.</p>
`,

  '/manuals': `
<h2>Handbücher</h2>
<p>Eingebaute Dokumentation und eigene hochgeladene Handbücher.</p>
<h3>Dokumentation</h3>
<p>Die eingebauten HTML-Dokumente (Handbuch, API-Referenz) sind schreibgeschützt und können nicht gelöscht werden.</p>
<h3>Eigene Handbücher</h3>
<p>Admins können eigene <code>.html</code>-Dateien hochladen (z.B. interne SOPs, Betriebshandbücher). Diese erscheinen in der Liste und können wieder gelöscht werden.</p>
<h3>Anzeige</h3>
<p>Klick auf eine Datei öffnet sie in der integrierten Vorschau rechts. Über den <b>Extern öffnen ↗</b>-Button in einem neuen Tab öffnen.</p>
`,
};

export function getHelp(path: string): string {
  // Exact match first, then prefix match
  if (helpTexts[path]) return helpTexts[path];
  const base = '/' + path.split('/')[1];
  return helpTexts[base] ?? `<h2>Hilfe</h2><p>Für diese Seite ist noch kein Hilfetext vorhanden.</p>`;
}

<template>
  <div>
    <!-- Header -->
    <div class="page-header">
      <div class="page-header-title">
        <h1>Receiver-Verwaltung</h1>
        <p>Empfänger-Status, Sender-Hosts, Lookup-Tabellen und Log-Verzeichnisse</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-ghost btn-sm" @click="loadAll" :disabled="loading">Aktualisieren</button>
      </div>
    </div>

    <div v-if="message" :class="['alert', messageType === 'error' ? 'alert-error' : 'alert-success']" style="margin-bottom:16px;">
      {{ message }}
    </div>

    <!-- ── Section 1: Status + Ports ───────────────────────────────────────── -->
    <div class="status-row mb-4">

      <!-- Service status -->
      <div class="card">
        <div class="card-header">rsyslog-Dienst</div>
        <div class="card-body">
          <div v-if="!svcStatus" class="text-muted text-sm">Wird geladen…</div>
          <template v-else>
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
              <span :class="['badge', svcStatus.status === 'active' ? 'badge-green' : 'badge-red']"
                style="font-size:12px;padding:3px 10px;">
                {{ svcStatus.status }}
              </span>
              <span class="text-sm text-muted">{{ svcStatus.sub_state }}</span>
            </div>
            <div class="meta-grid">
              <div class="meta-row"><span>Version</span><span class="font-mono">{{ svcStatus.version }}</span></div>
              <div class="meta-row"><span>PID</span><span class="font-mono">{{ svcStatus.main_pid }}</span></div>
              <div class="meta-row"><span>Neustarts</span><span>{{ svcStatus.n_restarts }}× seit letztem Start</span></div>
              <div v-if="svcStatus.uptime && svcStatus.uptime !== 'unknown'" class="meta-row">
                <span>Aktiv seit</span>
                <span class="font-mono" style="font-size:11px;">{{ formatUptime(svcStatus.uptime) }}</span>
              </div>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px;">
              <button class="btn btn-ghost btn-sm" @click="reloadSvc" :disabled="!canControl || actionSaving">Reload</button>
              <button class="btn btn-secondary btn-sm" @click="restartSvc" :disabled="!isAdmin || actionSaving">Restart</button>
              <button v-if="svcStatus.status !== 'active'" class="btn btn-primary btn-sm"
                @click="startSvc" :disabled="!isAdmin || actionSaving">Start</button>
              <button v-else class="btn btn-danger btn-sm"
                @click="stopSvc" :disabled="!isAdmin || actionSaving">Stop</button>
            </div>
          </template>
        </div>
      </div>

      <!-- Listening ports -->
      <div class="card">
        <div class="card-header">Konfigurierte Empfangs-Ports</div>
        <div class="card-body">
          <div v-if="!portsLoaded" class="text-muted text-sm">Wird geladen…</div>
          <div v-else-if="ports.length === 0" class="text-muted text-sm">
            Keine Input-Module konfiguriert.<br>
            <span style="font-size:11px;margin-top:6px;display:block;">
              Prüfe ob <code>module(load="imudp")</code> bzw. <code>imtcp</code>
              in rsyslog.conf oder /etc/rsyslog.d/ konfiguriert ist.
            </span>
          </div>
          <div v-else style="display:flex;flex-direction:column;gap:8px;">
            <div v-for="p in ports" :key="p.proto + p.local" style="display:flex;align-items:center;gap:8px;">
              <span :class="['badge', p.proto === 'udp' ? 'badge-blue' : 'badge-purple']"
                style="font-weight:700;font-size:11px;min-width:40px;justify-content:center;">
                {{ p.proto.toUpperCase() }}
              </span>
              <span class="font-mono text-sm">{{ p.local }}</span>
            </div>
          </div>
          <div class="text-muted" style="font-size:11px;margin-top:12px;">
            Standard: UDP :514 / TCP :514 für Remote-Syslog
          </div>
        </div>
      </div>

    </div>

    <!-- ── Section 2: Sender-Hosts (Heartbeat) ──────────────────────────────── -->
    <div class="card mb-4">
      <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
        <span>
          Sender-Hosts
          <span v-if="heartbeatHosts.length" class="count-badge">{{ heartbeatHosts.length }}</span>
        </span>
        <span class="text-muted" style="font-size:11px;">
          Warn &gt; {{ Math.round(heartbeatWarn / 60) }} min &nbsp;|&nbsp;
          Crit &gt; {{ Math.round(heartbeatCrit / 60) }} min
        </span>
      </div>
      <div v-if="!heartbeatLoaded" class="card-body text-muted text-sm">Wird geladen…</div>
      <div v-else-if="heartbeatHosts.length === 0" class="card-body text-muted text-sm">
        Noch keine Log-Dateien in <code>{{ syslogDataDir }}</code> — kein Host hat bisher Logs gesendet.
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Host</th>
            <th>Letzte Aktivität</th>
            <th>Status</th>
            <th>Log-Größe</th>
            <th>Verzeichnis</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in sortedHeartbeatHosts" :key="h.host">
            <td class="font-mono">{{ h.host }}</td>
            <td class="text-sm">{{ h.last_seen ? formatDateTime(h.last_seen) : '—' }}</td>
            <td>
              <span :class="['badge', heartbeatBadgeClass(h.status)]">{{ h.status }}</span>
            </td>
            <td class="text-sm font-mono">{{ dirSizeFor(h.host) }}</td>
            <td>
              <span v-if="dirFor(h.host)" :class="['badge', dirFor(h.host)!.perms_ok ? 'badge-green' : 'badge-yellow']">
                {{ dirFor(h.host)!.perms_ok ? '✓ OK' : '⚠ Rechte prüfen' }}
              </span>
              <button v-else-if="canControl" class="btn btn-ghost btn-sm"
                style="font-size:11px;padding:2px 8px;" @click="ensureDir(h.host)" :disabled="actionSaving">
                Verzeichnis anlegen
              </button>
              <span v-else class="text-muted text-sm">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Section 3: Lookup-Tabellen ──────────────────────────────────────── -->
    <div class="card mb-4">
      <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
        <span>Lookup-Tabellen (IP → Hostname Zuordnung)</span>
        <button v-if="canControl" class="btn btn-ghost btn-sm" @click="showCreateTable = !showCreateTable">
          + Neue Tabelle
        </button>
      </div>

      <!-- Create-table form -->
      <div v-if="showCreateTable" class="card-body" style="border-bottom:1px solid var(--border-soft);">
        <div style="display:flex;gap:8px;align-items:flex-end;">
          <div style="flex:1;">
            <label class="section-label" style="display:block;margin-bottom:4px;">
              Tabellenname (ohne <code>lookup_</code> Prefix und <code>.json</code>)
            </label>
            <input v-model="newTableName" class="input input-sm font-mono"
              placeholder="z.B. monitoring" @keyup.enter="createLookupTable" />
            <div class="text-muted" style="font-size:11px;margin-top:4px;">
              Erstellt: /etc/rsyslog.d/lookup_{{ newTableName || 'name' }}.json
            </div>
          </div>
          <button class="btn btn-primary btn-sm" @click="createLookupTable"
            :disabled="!newTableName.trim() || creatingTable">
            {{ creatingTable ? 'Erstelle…' : 'Erstellen' }}
          </button>
          <button class="btn btn-ghost btn-sm" @click="showCreateTable = false; newTableName = ''">
            Abbrechen
          </button>
        </div>
      </div>

      <div v-if="lookupTables.length === 0 && !loading" class="card-body text-muted text-sm">
        Keine Lookup-Tabellen gefunden unter /etc/rsyslog.d/lookup_*.json.
      </div>

      <!-- Per-table block -->
      <div v-for="t in lookupTables" :key="t.filename" class="lookup-block">
        <div class="lookup-block-header">
          <div>
            <span class="font-mono text-sm">{{ t.filename }}</span>
            <span class="text-muted" style="font-size:11px;margin-left:8px;">
              rsyslog-Variable: <code>{{ t.name }}</code>
            </span>
          </div>
          <span v-if="t.dirty" class="badge badge-yellow" style="font-size:10px;">ungespeichert</span>
        </div>
        <div style="overflow-x:auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width:45%;">IP-Adresse (Index)</th>
                <th style="width:45%;">Hostname (Wert)</th>
                <th v-if="canControl" style="width:10%;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(e, i) in t.entries" :key="i">
                <td>
                  <input v-if="canControl" v-model="e.index" class="input input-sm font-mono" style="width:100%;"
                    placeholder="192.168.1.1" @input="markDirty(t)" />
                  <span v-else class="font-mono text-sm">{{ e.index }}</span>
                </td>
                <td>
                  <input v-if="canControl" v-model="e.value" class="input input-sm font-mono" style="width:100%;"
                    placeholder="server01" @input="markDirty(t)" />
                  <span v-else class="font-mono text-sm">{{ e.value }}</span>
                </td>
                <td v-if="canControl" style="text-align:right;">
                  <button class="btn-del" title="Eintrag entfernen" @click="removeEntry(t, i)">✕</button>
                </td>
              </tr>
              <tr v-if="t.entries.length === 0">
                <td :colspan="canControl ? 3 : 2" class="text-muted text-sm" style="text-align:center;padding:12px;">
                  Keine Einträge — klicke "+ Eintrag" um einen Host hinzuzufügen.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="canControl" class="lookup-block-footer">
          <button class="btn btn-ghost btn-sm" @click="addEntry(t)">+ Eintrag</button>
          <button class="btn btn-primary btn-sm" @click="saveLookupTable(t)"
            :disabled="!t.dirty || saving">
            {{ saving ? 'Wird gespeichert…' : 'Speichern + rsyslog reload' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Section 4: Log-Verzeichnisse ────────────────────────────────────── -->
    <div class="card mb-4">
      <div class="card-header">Log-Verzeichnisse ({{ syslogDataDir }})</div>

      <div v-if="!dirsLoaded" class="card-body text-muted text-sm">Wird geladen…</div>
      <div v-else-if="logDirs.length === 0" class="card-body text-muted text-sm">
        Keine Verzeichnisse vorhanden. Noch keine Logs empfangen.
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Verzeichnis</th>
            <th>Größe</th>
            <th>Besitzer</th>
            <th>Rechte</th>
            <th>Status</th>
            <th v-if="canControl">Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in logDirs" :key="d.name">
            <td class="font-mono">{{ d.name }}</td>
            <td class="text-sm">{{ formatBytes(d.size_bytes) }}</td>
            <td class="font-mono text-sm">{{ d.owner }}:{{ d.group }}</td>
            <td class="font-mono text-sm">{{ d.mode }}</td>
            <td>
              <span :class="['badge', d.perms_ok ? 'badge-green' : 'badge-yellow']">
                {{ d.perms_ok ? '✓ OK' : '⚠ prüfen' }}
              </span>
            </td>
            <td v-if="canControl">
              <button v-if="!d.perms_ok" class="btn btn-ghost btn-sm"
                style="font-size:11px;padding:2px 8px;" @click="ensureDir(d.name)" :disabled="actionSaving">
                Rechte setzen
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- New directory -->
      <div v-if="canControl" class="card-body" style="border-top:1px solid var(--border-soft);">
        <div class="section-label" style="margin-bottom:6px;">Neues Host-Verzeichnis anlegen</div>
        <div style="display:flex;gap:8px;">
          <input v-model="newDirHost" class="input input-sm font-mono" style="flex:1;"
            placeholder="hostname oder IP" @keyup.enter="ensureNewDir" />
          <button class="btn btn-primary btn-sm" @click="ensureNewDir"
            :disabled="!newDirHost.trim() || actionSaving">
            Anlegen
          </button>
        </div>
        <div class="text-muted" style="font-size:11px;margin-top:4px;">
          Erstellt {{ syslogDataDir }}/{{ newDirHost || 'hostname' }}/ mit
          <code>chown syslog:adm</code> <code>chmod 755</code>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

const auth = useAuthStore();
const canControl = computed(() => auth.isAdmin || auth.isOperator);
const isAdmin    = computed(() => auth.isAdmin);

// ── State ─────────────────────────────────────────────────────────────────

const loading      = ref(false);
const actionSaving = ref(false);
const saving       = ref(false);
const message      = ref('');
const messageType  = ref<'success' | 'error'>('success');

interface ServiceStatus {
  service: string; status: string; enabled: boolean; version: string;
  uptime: string; n_restarts: number; main_pid: string; sub_state: string;
}
interface ReceiverPort { proto: string; local: string; port: string; }
interface HeartbeatHost {
  host: string; last_seen: string | null; age_seconds: number | null;
  status: 'ok' | 'warn' | 'crit' | 'unknown';
}
interface LogDir {
  name: string; path: string; size_bytes: number;
  mode: string; owner: string; group: string; perms_ok: boolean;
}
interface LookupEntry { index: string; value: string; }
interface LookupTable { filename: string; name: string; entries: LookupEntry[]; dirty?: boolean; }

const svcStatus       = ref<ServiceStatus | null>(null);
const ports           = ref<ReceiverPort[]>([]);
const portsLoaded     = ref(false);
const heartbeatHosts  = ref<HeartbeatHost[]>([]);
const heartbeatWarn   = ref(900);
const heartbeatCrit   = ref(3600);
const heartbeatLoaded = ref(false);
const logDirs         = ref<LogDir[]>([]);
const dirsLoaded      = ref(false);
const syslogDataDir   = ref('/data/syslog');
const lookupTables    = ref<LookupTable[]>([]);

const showCreateTable = ref(false);
const newTableName    = ref('');
const creatingTable   = ref(false);
const newDirHost      = ref('');

// ── Flash ─────────────────────────────────────────────────────────────────

function flash(msg: string, type: 'success' | 'error' = 'success') {
  message.value = msg;
  messageType.value = type;
  setTimeout(() => { message.value = ''; }, 4500);
}

// ── Load ──────────────────────────────────────────────────────────────────

async function loadStatus() {
  try {
    const res = await apiClient.get('/rsyslog/status');
    svcStatus.value = res.data;
  } catch { flash('Dienst-Status konnte nicht geladen werden.', 'error'); }
}

async function loadPorts() {
  try {
    const res = await apiClient.get('/rsyslog/receiver-ports');
    ports.value = res.data.ports ?? [];
  } catch { /* non-critical */ }
  finally { portsLoaded.value = true; }
}

async function loadHeartbeat() {
  try {
    const res = await apiClient.get('/rsyslog/heartbeat');
    heartbeatHosts.value  = res.data.hosts ?? [];
    heartbeatWarn.value   = res.data.warn_threshold ?? 900;
    heartbeatCrit.value   = res.data.crit_threshold ?? 3600;
  } catch { flash('Heartbeat-Daten konnten nicht geladen werden.', 'error'); }
  finally { heartbeatLoaded.value = true; }
}

async function loadLogDirs() {
  try {
    const res = await apiClient.get('/rsyslog/log-dirs');
    logDirs.value       = res.data.dirs ?? [];
    syslogDataDir.value = res.data.base_dir ?? '/data/syslog';
  } catch { /* non-critical */ }
  finally { dirsLoaded.value = true; }
}

async function loadLookupTables() {
  try {
    const res = await apiClient.get('/rsyslog/lookup-tables');
    lookupTables.value = (res.data.tables ?? []).map((t: LookupTable) => ({
      ...t,
      entries: t.entries.map((e: LookupEntry) => ({ ...e })),
      dirty: false,
    }));
  } catch { flash('Lookup-Tabellen konnten nicht geladen werden.', 'error'); }
}

async function loadAll() {
  loading.value = true;
  await Promise.allSettled([
    loadStatus(),
    loadPorts(),
    loadHeartbeat(),
    loadLogDirs(),
    loadLookupTables(),
  ]);
  loading.value = false;
}

// ── Service actions ───────────────────────────────────────────────────────

async function reloadSvc() {
  actionSaving.value = true;
  try {
    await apiClient.post('/rsyslog/reload');
    flash('Dienst erfolgreich neu geladen.');
    await loadStatus();
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Reload fehlgeschlagen.', 'error'); }
  finally { actionSaving.value = false; }
}

async function restartSvc() {
  if (!confirm('rsyslog wirklich neu starten?')) return;
  actionSaving.value = true;
  try {
    await apiClient.post('/rsyslog/restart');
    flash('Dienst neu gestartet.');
    setTimeout(loadStatus, 2000);
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Restart fehlgeschlagen.', 'error'); }
  finally { actionSaving.value = false; }
}

async function startSvc() {
  actionSaving.value = true;
  try {
    await apiClient.post('/rsyslog/start');
    flash('Dienst gestartet.');
    setTimeout(loadStatus, 2000);
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Start fehlgeschlagen.', 'error'); }
  finally { actionSaving.value = false; }
}

async function stopSvc() {
  if (!confirm('rsyslog wirklich stoppen?')) return;
  actionSaving.value = true;
  try {
    await apiClient.post('/rsyslog/stop');
    flash('Dienst gestoppt.');
    setTimeout(loadStatus, 2000);
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Stop fehlgeschlagen.', 'error'); }
  finally { actionSaving.value = false; }
}

// ── Lookup table actions ──────────────────────────────────────────────────

function addEntry(t: LookupTable) {
  t.entries.push({ index: '', value: '' });
  t.dirty = true;
}

function removeEntry(t: LookupTable, i: number) {
  t.entries.splice(i, 1);
  t.dirty = true;
}

function markDirty(t: LookupTable) { t.dirty = true; }

async function saveLookupTable(t: LookupTable) {
  saving.value = true;
  try {
    const clean = t.entries.filter(e => e.index.trim());
    await apiClient.put(`/rsyslog/lookup-tables/${t.filename}`, clean);
    t.entries = clean;
    t.dirty = false;
    flash(`${t.filename} gespeichert. rsyslog wird neu geladen.`);
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Speichern fehlgeschlagen.', 'error'); }
  finally { saving.value = false; }
}

async function createLookupTable() {
  const name = newTableName.value.trim().replace(/[^a-zA-Z0-9_\-]/g, '_');
  if (!name) return;
  const filename = `lookup_${name}.json`;
  creatingTable.value = true;
  try {
    await apiClient.post('/rsyslog/lookup-tables', null, { params: { filename } });
    newTableName.value = '';
    showCreateTable.value = false;
    flash(`${filename} erstellt.`);
    await loadLookupTables();
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Erstellen fehlgeschlagen.', 'error'); }
  finally { creatingTable.value = false; }
}

// ── Log-dir actions ───────────────────────────────────────────────────────

async function ensureDir(host: string) {
  const h = host.trim();
  if (!h) return;
  actionSaving.value = true;
  try {
    const res = await apiClient.post('/rsyslog/log-dirs/ensure', { host: h });
    flash(res.data.message ?? `${h}: OK`);
    await loadLogDirs();
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler beim Anlegen.', 'error'); }
  finally { actionSaving.value = false; }
}

async function ensureNewDir() {
  await ensureDir(newDirHost.value);
  newDirHost.value = '';
}

// ── Computed / helpers ────────────────────────────────────────────────────

const sortedHeartbeatHosts = computed(() =>
  [...heartbeatHosts.value].sort((a, b) => {
    const order: Record<string, number> = { crit: 0, warn: 1, ok: 2, unknown: 3 };
    return (order[a.status] ?? 3) - (order[b.status] ?? 3);
  })
);

function dirFor(host: string): LogDir | undefined {
  return logDirs.value.find(d => d.name === host);
}

function dirSizeFor(host: string): string {
  const d = logDirs.value.find(d => d.name === host);
  return d ? formatBytes(d.size_bytes) : '—';
}

function heartbeatBadgeClass(status: string): string {
  return { ok: 'badge-green', warn: 'badge-yellow', crit: 'badge-red', unknown: 'badge-gray' }[status] ?? 'badge-gray';
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1_073_741_824) return `${(bytes / 1_048_576).toFixed(1)} MB`;
  return `${(bytes / 1_073_741_824).toFixed(2)} GB`;
}

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' });
  } catch { return iso; }
}

function formatUptime(ts: string): string {
  if (!ts || ts === 'unknown') return 'unbekannt';
  try {
    const dateStr = ts.match(/\d{4}-\d{2}-\d{2}/)?.[0];
    const timeStr = ts.match(/\d{2}:\d{2}:\d{2}/)?.[0];
    if (dateStr && timeStr) {
      const d = new Date(`${dateStr}T${timeStr}Z`);
      if (!isNaN(d.getTime())) {
        return d.toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }) + ' UTC';
      }
    }
  } catch { /* fall through */ }
  return ts;
}

onMounted(loadAll);
</script>

<style scoped>
.mb-4     { margin-bottom: 16px; }
.text-sm  { font-size: 12px; }
.text-muted { color: var(--text-muted); }
.font-mono  { font-family: ui-monospace, monospace; }

/* Top status row: two equal cards */
.status-row { display: flex; gap: 16px; }
.status-row > .card { flex: 1; min-width: 0; }
@media (max-width: 700px) { .status-row { flex-direction: column; } }

/* Meta key/value grid inside status card */
.meta-grid { display: flex; flex-direction: column; gap: 5px; margin-bottom: 12px; }
.meta-row  { display: flex; justify-content: space-between; align-items: baseline; font-size: 12px; }
.meta-row > span:first-child { color: var(--text-muted); }

/* Lookup table blocks */
.lookup-block { border-top: 1px solid var(--border-soft); }
.lookup-block-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 16px; background: var(--bg-subtle, #f8fafc);
}
.lookup-block-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; background: var(--bg-subtle, #f8fafc);
  border-top: 1px solid var(--border-soft);
}

/* Remove-entry button */
.btn-del {
  background: none; border: none; cursor: pointer;
  color: var(--text-muted); padding: 2px 5px; border-radius: 3px; font-size: 12px;
}
.btn-del:hover { color: #991b1b; background: #fee2e2; }

/* Host count badge */
.count-badge {
  background: var(--ks-100); color: var(--ks-700);
  font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 9px;
  display: inline-block; margin-left: 6px;
}

/* Reuse section label style */
.section-label {
  font-size: 11px; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .05em;
}

/* badge-purple (TCP) not in global css */
.badge-purple { background: #ede9fe; color: #5b21b6; }
</style>

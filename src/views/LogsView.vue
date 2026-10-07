<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Log-Analyse</h1>
        <p>Remote-Syslog-Einträge durchsuchen und filtern</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary btn-sm" @click="loadLogs" :disabled="loading">
          {{ loading ? 'Lädt …' : 'Aktualisieren' }}
        </button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="card mb-4 filter-bar">
      <div class="filter-row">
        <!-- Host filter -->
        <div class="filter-group">
          <label class="filter-label">Host</label>
          <select class="select-inline" v-model="filterHost" @change="loadLogs">
            <option value="">— alle —</option>
            <option v-for="h in availableHosts" :key="h" :value="h">{{ h }}</option>
          </select>
        </div>

        <!-- Severity filter -->
        <div class="filter-group">
          <label class="filter-label">Schweregrad</label>
          <MultiSelect v-model="filterSeverity" :options="SEVERITY_OPTIONS" @update:modelValue="loadLogs" />
        </div>

        <!-- Facility filter -->
        <div class="filter-group">
          <label class="filter-label">Facility</label>
          <MultiSelect v-model="filterFacility" :options="FACILITY_OPTIONS" @update:modelValue="loadLogs" />
        </div>

        <!-- Program filter -->
        <div class="filter-group" style="flex:2;">
          <label class="filter-label">Programm</label>
          <input
            class="input input-sm"
            v-model="filterProgram"
            placeholder="z.B. sshd, kernel …"
            @input="scheduleLoad"
            style="width:100%;"
          />
        </div>

        <!-- Search -->
        <div class="filter-group" style="flex:3;">
          <label class="filter-label">Suche</label>
          <input
            class="input input-sm"
            v-model="searchText"
            placeholder="Freitext-Suche in Nachricht …"
            @input="scheduleLoad"
            style="width:100%;"
          />
        </div>

        <!-- Time range -->
        <div class="filter-group">
          <label class="filter-label">Zeitraum</label>
          <select class="select-inline" v-model="timePreset" @change="onPresetChange">
            <option value="">— alle —</option>
            <option value="1h">Letzte Stunde</option>
            <option value="6h">Letzte 6 Stunden</option>
            <option value="24h">Letzte 24 Stunden</option>
            <option value="7d">Letzte 7 Tage</option>
            <option value="custom">Benutzerdefiniert …</option>
          </select>
        </div>
        <template v-if="timePreset === 'custom'">
          <div class="filter-group">
            <label class="filter-label">Von</label>
            <input type="datetime-local" step="1" class="input input-sm" v-model="timeFrom" @change="loadLogs" />
          </div>
          <div class="filter-group">
            <label class="filter-label">Bis</label>
            <input type="datetime-local" step="1" class="input input-sm" v-model="timeTo" @change="loadLogs" />
          </div>
        </template>

        <!-- Limit -->
        <div class="filter-group" style="min-width:80px;">
          <label class="filter-label">Max. Zeilen</label>
          <input
            type="number"
            class="input input-sm"
            v-model.number="limitVal"
            min="10"
            max="2000"
            @change="loadLogs"
            style="width:70px;"
          />
        </div>
      </div>
    </div>

    <!-- Log table -->
    <div class="card">
      <div class="card-header">
        <span>Log-Einträge</span>
        <span class="text-muted text-sm">
          <span v-if="truncated" class="trunc-note" title="Die Suche hat pro Datei nur die neuesten Zeilen durchsucht. Zeitraum oder Host eingrenzen, um gezielt weiter zurückzusuchen.">Suche begrenzt · </span>{{ filtered.length }} Einträge
        </span>
      </div>
      <div class="log-table-wrap">
        <table class="data-table log-table" v-if="filtered.length">
          <thead>
            <tr>
              <th style="width:140px;">Zeitstempel</th>
              <th style="width:120px;">Host</th>
              <th style="width:80px;">Severity</th>
              <th style="width:80px;">Facility</th>
              <th style="width:110px;">Programm</th>
              <th>Nachricht</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(e, i) in filtered"
              :key="i"
              :class="severityRowClass(e.syslogseverity ?? e.severity)"
            >
              <td class="ts-cell">{{ formatTs(e.timereported ?? e.timestamp ?? '') }}</td>
              <td class="font-mono text-sm">{{ e.hostname ?? e.host ?? '—' }}</td>
              <td>
                <span class="sev-badge" :class="severityBadge(e.syslogseverity ?? e.severity)">
                  {{ severityLabel(e.syslogseverity ?? e.severity) }}
                </span>
              </td>
              <td class="text-muted text-sm">{{ e.syslogfacility_text ?? e.facility ?? '—' }}</td>
              <td class="font-mono text-sm">{{ e.programname ?? e.program ?? '—' }}</td>
              <td class="msg-cell">
                <span v-html="highlightSearch(e.msg ?? e.message ?? e.raw ?? '')"></span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else-if="loading" class="log-empty">Lade …</div>
        <div v-else class="log-empty text-muted">
          Keine Einträge gefunden.
          <span v-if="searchText || filterSeverity.length || filterFacility.length || filterProgram || timePreset">
            Filter zurücksetzen um alle anzuzeigen.
          </span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import MultiSelect from '../components/MultiSelect.vue';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

const auth = useAuthStore();

const allEntries     = ref<Record<string, unknown>[]>([]);
const availableHosts = ref<string[]>([]);
const loading        = ref(false);

const filterHost     = ref('');
const filterSeverity = ref<string[]>([]);
const filterFacility = ref<string[]>([]);
const filterProgram  = ref('');
const searchText     = ref('');
const limitVal       = ref(500);
const timePreset     = ref('');
const timeFrom       = ref('');
const timeTo         = ref('');
const truncated      = ref(false);

const SEVERITY_OPTIONS = [
  { value: '0', label: '0 emerg' },  { value: '1', label: '1 alert' },
  { value: '2', label: '2 crit' },   { value: '3', label: '3 err' },
  { value: '4', label: '4 warning' }, { value: '5', label: '5 notice' },
  { value: '6', label: '6 info' },   { value: '7', label: '7 debug' },
];
const FACILITY_OPTIONS = [
  'kern', 'user', 'mail', 'daemon', 'auth', 'syslog', 'lpr', 'news', 'cron',
  'local0', 'local1', 'local2', 'local3', 'local4', 'local5', 'local6', 'local7',
].map(f => ({ value: f, label: f }));

// Alle Filter werden serverseitig angewendet (vor dem Zeilenlimit), damit auch seltene
// Treffer gefunden werden und Einträge aller Hosts zeitlich gemischt erscheinen.
const filtered = computed(() => allEntries.value);

// Texteingaben entprellen, damit nicht jeder Tastendruck einen Request auslöst
let debounceTimer: ReturnType<typeof setTimeout> | undefined;
function scheduleLoad() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadLogs, 400);
}
onBeforeUnmount(() => clearTimeout(debounceTimer));

async function loadHosts() {
  try {
    const res = await apiClient.get('/rsyslog/remote-logs/hosts');
    availableHosts.value = res.data.hosts ?? [];
  } catch { /* ignore */ }
}

const PRESET_MS: Record<string, number> = {
  '1h': 3_600_000, '6h': 6 * 3_600_000, '24h': 24 * 3_600_000, '7d': 7 * 24 * 3_600_000,
};

function onPresetChange() {
  loadLogs();
}

// datetime-local (browser local time) -> ISO/UTC
function localToIso(v: string): string | undefined {
  if (!v) return undefined;
  const d = new Date(v);
  return isNaN(d.getTime()) ? undefined : d.toISOString();
}

let requestSeq = 0;

async function loadLogs() {
  clearTimeout(debounceTimer);
  const seq = ++requestSeq;
  loading.value = true;
  try {
    await auth.initialize();
    const params: Record<string, unknown> = { limit: limitVal.value };
    if (filterHost.value) params.host = filterHost.value;
    if (filterSeverity.value.length) params.severity = filterSeverity.value.join(',');
    if (filterFacility.value.length) params.facility = filterFacility.value.join(',');
    if (filterProgram.value.trim()) params.program = filterProgram.value.trim();
    if (searchText.value.trim()) params.q = searchText.value.trim();
    if (timePreset.value === 'custom') {
      const since = localToIso(timeFrom.value);
      const until = localToIso(timeTo.value);
      if (since) params.since = since;
      if (until) params.until = until;
    } else if (PRESET_MS[timePreset.value]) {
      params.since = new Date(Date.now() - PRESET_MS[timePreset.value]).toISOString();
    }
    const res = await apiClient.get('/rsyslog/remote-logs', { params });
    if (seq !== requestSeq) return; // veraltete Antwort ignorieren
    allEntries.value = res.data.entries ?? [];
    truncated.value = !!res.data.truncated;
  } catch {
    if (seq !== requestSeq) return;
    allEntries.value = [];
    truncated.value = false;
  } finally {
    if (seq === requestSeq) loading.value = false;
  }
}

// ── formatting helpers ───────────────────────────────────────────────────────

function formatTs(ts: string): string {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString('de-DE', {
      day: '2-digit', month: '2-digit', year: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch { return ts; }
}

const SEV_LABELS: Record<number, string> = {
  0: 'emerg', 1: 'alert', 2: 'crit', 3: 'err',
  4: 'warn', 5: 'notice', 6: 'info', 7: 'debug',
};

function severityLabel(sev: unknown): string {
  const n = Number(sev);
  return isNaN(n) ? String(sev ?? '?') : (SEV_LABELS[n] ?? String(n));
}

function severityBadge(sev: unknown): string {
  const n = Number(sev);
  if (n <= 2) return 'sev-crit';
  if (n === 3) return 'sev-err';
  if (n === 4) return 'sev-warn';
  if (n === 5) return 'sev-notice';
  return 'sev-info';
}

function severityRowClass(sev: unknown): string {
  const n = Number(sev);
  if (n <= 2) return 'row-crit';
  if (n === 3) return 'row-err';
  if (n === 4) return 'row-warn';
  return '';
}

function highlightSearch(text: string): string {
  const msg = String(text);
  if (!searchText.value) return escHtml(msg);
  const q = searchText.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return escHtml(msg).replace(
    new RegExp(`(${q})`, 'gi'),
    '<mark>$1</mark>',
  );
}

function escHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

onMounted(async () => {
  await loadHosts();
  await loadLogs();
});
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.font-mono { font-family: ui-monospace, monospace; }
.text-sm { font-size: 12px; }

.filter-bar { padding: 12px 16px; }
.filter-row {
  display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end;
}
.filter-group { display: flex; flex-direction: column; gap: 3px; min-width: 100px; }
.filter-label { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em; }

.log-table-wrap { max-height: 65vh; overflow-y: auto; }
.log-table { font-size: 12px; }
.log-table th { position: sticky; top: 0; background: var(--surface); z-index: 1; }
.ts-cell { white-space: nowrap; font-family: ui-monospace, monospace; color: var(--text-muted); font-size: 11px; }
.msg-cell { word-break: break-word; max-width: 500px; }
.log-empty { padding: 24px; text-align: center; font-size: 13px; }

/* Farben als Variablen; Dark Mode überschreibt sie (wie styles.css via prefers-color-scheme) */
.log-table-wrap, .log-table {
  --row-crit: #fef2f2; --row-err: #fff7ed; --row-warn: #fefce8;
  --sev-crit-bg: #fee2e2; --sev-crit-fg: #991b1b;
  --sev-err-bg: #ffedd5;  --sev-err-fg: #9a3412;
  --sev-warn-bg: #fef9c3; --sev-warn-fg: #854d0e;
  --sev-notice-bg: #e0f2fe; --sev-notice-fg: #075985;
  --sev-info-bg: #f1f5f9; --sev-info-fg: #475569;
  --mark-bg: #fde68a; --mark-fg: inherit;
}
@media (prefers-color-scheme: dark) {
  .log-table-wrap, .log-table {
    --row-crit: rgba(239, 68, 68, .16); --row-err: rgba(249, 115, 22, .14); --row-warn: rgba(234, 179, 8, .12);
    --sev-crit-bg: #450a0a; --sev-crit-fg: #fca5a5;
    --sev-err-bg: #431407;  --sev-err-fg: #fdba74;
    --sev-warn-bg: #422006; --sev-warn-fg: #fde68a;
    --sev-notice-bg: #0c2d48; --sev-notice-fg: #7dd3fc;
    --sev-info-bg: #1e293b; --sev-info-fg: #94a3b8;
    --mark-bg: #854d0e; --mark-fg: #fef9c3;
  }
}

/* Row severity tints */
.row-crit td { background: var(--row-crit); }
.row-err  td { background: var(--row-err); }
.row-warn td { background: var(--row-warn); }

/* Severity badges */
.sev-badge {
  display: inline-block; padding: 1px 6px; border-radius: 4px;
  font-size: 10px; font-weight: 700; font-family: ui-monospace, monospace; white-space: nowrap;
}
.sev-crit   { background: var(--sev-crit-bg);   color: var(--sev-crit-fg); }
.sev-err    { background: var(--sev-err-bg);    color: var(--sev-err-fg); }
.sev-warn   { background: var(--sev-warn-bg);   color: var(--sev-warn-fg); }
.sev-notice { background: var(--sev-notice-bg); color: var(--sev-notice-fg); }
.sev-info   { background: var(--sev-info-bg);   color: var(--sev-info-fg); }

/* Search highlight */
:deep(mark) { background: var(--mark-bg); color: var(--mark-fg); border-radius: 2px; padding: 0 1px; }

.trunc-note { color: #b45309; font-weight: 600; cursor: help; }
@media (prefers-color-scheme: dark) { .trunc-note { color: #fbbf24; } }
</style>

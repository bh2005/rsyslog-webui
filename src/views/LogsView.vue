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
          <select class="select-inline" v-model="filterSeverity" @change="applyFilters">
            <option value="">— alle —</option>
            <option value="0">0 emerg</option>
            <option value="1">1 alert</option>
            <option value="2">2 crit</option>
            <option value="3">3 err</option>
            <option value="4">4 warning</option>
            <option value="5">5 notice</option>
            <option value="6">6 info</option>
            <option value="7">7 debug</option>
          </select>
        </div>

        <!-- Facility filter -->
        <div class="filter-group">
          <label class="filter-label">Facility</label>
          <select class="select-inline" v-model="filterFacility" @change="applyFilters">
            <option value="">— alle —</option>
            <option value="kern">kern</option>
            <option value="user">user</option>
            <option value="mail">mail</option>
            <option value="daemon">daemon</option>
            <option value="auth">auth</option>
            <option value="syslog">syslog</option>
            <option value="lpr">lpr</option>
            <option value="news">news</option>
            <option value="cron">cron</option>
            <option value="local0">local0</option>
            <option value="local1">local1</option>
            <option value="local2">local2</option>
            <option value="local3">local3</option>
            <option value="local4">local4</option>
            <option value="local5">local5</option>
            <option value="local6">local6</option>
            <option value="local7">local7</option>
          </select>
        </div>

        <!-- Program filter -->
        <div class="filter-group" style="flex:2;">
          <label class="filter-label">Programm</label>
          <input
            class="input input-sm"
            v-model="filterProgram"
            placeholder="z.B. sshd, kernel …"
            @input="applyFilters"
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
            @input="applyFilters"
            style="width:100%;"
          />
        </div>

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
        <span class="text-muted text-sm">{{ filtered.length }} Einträge{{ totalLoaded !== filtered.length ? ` (von ${totalLoaded} geladen)` : '' }}</span>
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
          <span v-if="searchText || filterSeverity || filterFacility || filterProgram">
            Filter zurücksetzen um alle anzuzeigen.
          </span>
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

const allEntries     = ref<Record<string, unknown>[]>([]);
const availableHosts = ref<string[]>([]);
const loading        = ref(false);

const filterHost     = ref('');
const filterSeverity = ref('');
const filterFacility = ref('');
const filterProgram  = ref('');
const searchText     = ref('');
const limitVal       = ref(500);

const totalLoaded = computed(() => allEntries.value.length);

// Client-side filtering (host filter is server-side, the rest client-side)
const filtered = computed(() => {
  let list = allEntries.value;

  if (filterSeverity.value !== '') {
    const sev = Number(filterSeverity.value);
    list = list.filter(e => {
      const s = Number(e.syslogseverity ?? e.severity ?? 99);
      return s === sev;
    });
  }
  if (filterFacility.value) {
    const fac = filterFacility.value.toLowerCase();
    list = list.filter(e =>
      String(e.syslogfacility_text ?? e.facility ?? '').toLowerCase() === fac,
    );
  }
  if (filterProgram.value) {
    const prog = filterProgram.value.toLowerCase();
    list = list.filter(e =>
      String(e.programname ?? e.program ?? '').toLowerCase().includes(prog),
    );
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase();
    list = list.filter(e =>
      String(e.msg ?? e.message ?? e.raw ?? '').toLowerCase().includes(q),
    );
  }
  return list;
});

function applyFilters() {
  // Reactivity handles it via computed — called on input for searchText / program.
}

async function loadHosts() {
  try {
    const res = await apiClient.get('/rsyslog/remote-logs/hosts');
    availableHosts.value = res.data.hosts ?? [];
  } catch { /* ignore */ }
}

async function loadLogs() {
  loading.value = true;
  try {
    await auth.initialize();
    const params: Record<string, unknown> = { limit: limitVal.value };
    if (filterHost.value) params.host = filterHost.value;
    const res = await apiClient.get('/rsyslog/remote-logs', { params });
    allEntries.value = res.data.entries ?? [];
  } catch {
    allEntries.value = [];
  } finally {
    loading.value = false;
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
.log-table th { position: sticky; top: 0; background: var(--bg-muted); z-index: 1; }
.ts-cell { white-space: nowrap; font-family: ui-monospace, monospace; color: var(--text-muted); font-size: 11px; }
.msg-cell { word-break: break-word; max-width: 500px; }
.log-empty { padding: 24px; text-align: center; font-size: 13px; }

/* Row severity tints */
.row-crit td { background: #fef2f2; }
.row-err  td { background: #fff7ed; }
.row-warn td { background: #fefce8; }

/* Severity badges */
.sev-badge {
  display: inline-block; padding: 1px 6px; border-radius: 4px;
  font-size: 10px; font-weight: 700; font-family: ui-monospace, monospace; white-space: nowrap;
}
.sev-crit   { background: #fee2e2; color: #991b1b; }
.sev-err    { background: #ffedd5; color: #9a3412; }
.sev-warn   { background: #fef9c3; color: #854d0e; }
.sev-notice { background: #e0f2fe; color: #075985; }
.sev-info   { background: #f1f5f9; color: #475569; }

/* Search highlight */
:deep(mark) { background: #fde68a; color: inherit; border-radius: 2px; padding: 0 1px; }
</style>

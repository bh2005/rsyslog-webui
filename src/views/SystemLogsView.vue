<template>
  <div class="syslogs-page">

    <div class="page-header">
      <div class="page-header-title">
        <h1>System-Logs</h1>
        <p>Backend-Anwendungslogs (In-Memory-Ringpuffer, max. 2000 Einträge)</p>
      </div>
      <div class="flex gap-2">
        <label class="auto-refresh-label">
          <input type="checkbox" v-model="autoRefresh" />
          Auto (5s)
        </label>
        <button class="btn btn-ghost btn-sm" :disabled="loading" @click="load">
          {{ loading ? 'Lädt…' : 'Aktualisieren' }}
        </button>
        <button class="btn btn-ghost btn-sm" @click="downloadTXT" title="Als TXT herunterladen">↓ TXT</button>
        <button class="btn btn-ghost btn-sm" @click="downloadCSV" title="Als CSV herunterladen">↓ CSV</button>
        <button class="btn btn-ghost btn-sm" @click="downloadJSON" title="Als JSON herunterladen">↓ JSON</button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <div class="level-btns">
        <button
          v-for="l in levels" :key="l.value"
          class="level-btn"
          :class="[l.cls, { active: levelFilter === l.value }]"
          @click="levelFilter = l.value"
        >
          {{ l.label }}
          <span class="level-count">{{ countFor(l.value) }}</span>
        </button>
      </div>
      <input v-model="search" class="input input-sm search-input" placeholder="Suchen… (Logger, Nachricht)" />
      <label class="auto-refresh-label">
        <input type="checkbox" v-model="autoScroll" />
        Auto-Scroll
      </label>
    </div>

    <!-- Log table (dark terminal style) -->
    <div ref="tableWrap" class="log-terminal">
      <table class="log-table">
        <thead>
          <tr>
            <th class="col-ts">Zeit</th>
            <th class="col-level">Level</th>
            <th class="col-logger">Logger</th>
            <th class="col-msg">Nachricht</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(e, i) in filtered" :key="i">
            <tr
              class="log-row"
              :class="[rowClass(e.level), e.exc ? 'has-exc' : '']"
              @click="expandedIdx = expandedIdx === i ? null : i"
            >
              <td class="col-ts log-ts">{{ fmtTs(e.ts) }}</td>
              <td class="col-level">
                <span class="level-badge" :class="levelBadge(e.level)">{{ e.level }}</span>
              </td>
              <td class="col-logger log-logger">{{ e.logger }}</td>
              <td class="col-msg log-msg" :class="msgClass(e.level)">
                {{ e.message }}
                <span v-if="e.exc" class="exc-hint">▸ traceback</span>
              </td>
            </tr>
            <tr v-if="expandedIdx === i && e.exc" class="exc-row">
              <td colspan="4">
                <pre class="exc-pre">{{ e.exc }}</pre>
              </td>
            </tr>
          </template>
          <tr v-if="!filtered.length && !loading">
            <td colspan="4" class="log-empty">
              {{ search || levelFilter !== 'ALL' ? 'Keine Einträge für diesen Filter.' : 'Noch keine Log-Einträge.' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Footer -->
    <div class="log-footer">
      <span>{{ filtered.length }} / {{ entries.length }} Einträge</span>
      <span v-if="lastRefresh">Zuletzt: {{ lastRefresh }}</span>
      <span v-if="countFor('ERROR') > 0" class="footer-error">{{ countFor('ERROR') }} ERROR</span>
      <span v-if="countFor('CRITICAL') > 0" class="footer-error">{{ countFor('CRITICAL') }} CRITICAL</span>
      <span v-if="countFor('WARNING') > 0" class="footer-warn">{{ countFor('WARNING') }} WARNING</span>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { apiClient } from '../api';

interface LogEntry { ts: string; level: string; logger: string; message: string; exc?: string; }

const entries     = ref<LogEntry[]>([]);
const loading     = ref(false);
const levelFilter = ref('ALL');
const search      = ref('');
const autoRefresh = ref(false);
const autoScroll  = ref(true);
const expandedIdx = ref<number | null>(null);
const lastRefresh = ref('');
const tableWrap   = ref<HTMLElement | null>(null);
let timer: ReturnType<typeof setInterval> | null = null;

const levels = [
  { value: 'ALL',      label: 'Alle',     cls: 'lvl-all' },
  { value: 'ERROR',    label: 'Error',    cls: 'lvl-error' },
  { value: 'CRITICAL', label: 'Critical', cls: 'lvl-critical' },
  { value: 'WARNING',  label: 'Warning',  cls: 'lvl-warning' },
  { value: 'INFO',     label: 'Info',     cls: 'lvl-info' },
  { value: 'DEBUG',    label: 'Debug',    cls: 'lvl-debug' },
];

const filtered = computed(() => {
  let list = entries.value;
  if (levelFilter.value !== 'ALL') list = list.filter(e => e.level === levelFilter.value);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    list = list.filter(e => e.message.toLowerCase().includes(q) || e.logger.toLowerCase().includes(q));
  }
  return list;
});

function countFor(level: string) {
  if (level === 'ALL') return entries.value.length;
  return entries.value.filter(e => e.level === level).length;
}

function fmtTs(ts: string) {
  return ts ? ts.replace('T', ' ').replace('Z', '') : '—';
}

function levelBadge(level: string): string {
  return ({ ERROR: 'badge-level-error', CRITICAL: 'badge-level-critical',
            WARNING: 'badge-level-warning', INFO: 'badge-level-info',
            DEBUG: 'badge-level-debug' } as Record<string,string>)[level] ?? 'badge-level-debug';
}

function rowClass(level: string): string {
  return ({ ERROR: 'row-error', CRITICAL: 'row-critical', WARNING: 'row-warning' } as Record<string,string>)[level] ?? '';
}

function msgClass(level: string): string {
  return ({ ERROR: 'msg-error', CRITICAL: 'msg-critical', WARNING: 'msg-warning',
            INFO: 'msg-info', DEBUG: 'msg-debug' } as Record<string,string>)[level] ?? 'msg-info';
}

async function load() {
  loading.value = true;
  try {
    const res = await apiClient.get('/syslogs', { params: { level: 'ALL', limit: 2000 } });
    entries.value = res.data;
    lastRefresh.value = new Date().toLocaleTimeString('de-DE');
    if (autoScroll.value) {
      await nextTick();
      if (tableWrap.value) tableWrap.value.scrollTop = tableWrap.value.scrollHeight;
    }
  } catch { /* ignore */ } finally { loading.value = false; }
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function downloadTXT() {
  const lines = filtered.value.map(e =>
    `${e.ts} [${e.level.padEnd(8)}] ${e.logger} — ${e.message}${e.exc ? '\n' + e.exc : ''}`
  ).join('\n');
  triggerDownload(new Blob([lines], { type: 'text/plain' }),
    `rsyslog-manager-syslogs-${new Date().toISOString().slice(0,19)}.txt`);
}

function downloadCSV() {
  const header = 'Zeit,Level,Logger,Nachricht';
  const rows = filtered.value.map(e =>
    [e.ts, e.level, e.logger, `"${(e.message ?? '').replace(/"/g, '""')}"`].join(',')
  );
  triggerDownload(new Blob([[header, ...rows].join('\n')], { type: 'text/csv' }),
    `rsyslog-manager-syslogs-${new Date().toISOString().slice(0,10)}.csv`);
}

function downloadJSON() {
  const payload = filtered.value.map(e => ({
    ts: e.ts, level: e.level, logger: e.logger, message: e.message,
    ...(e.exc ? { traceback: e.exc } : {}),
  }));
  triggerDownload(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }),
    `rsyslog-manager-syslogs-${new Date().toISOString().slice(0,10)}.json`);
}

watch(autoRefresh, (on) => {
  if (timer) { clearInterval(timer); timer = null; }
  if (on) timer = setInterval(load, 5000);
});

onMounted(load);
onUnmounted(() => { if (timer) clearInterval(timer); });
</script>

<style scoped>
.syslogs-page { display: flex; flex-direction: column; height: 100%; gap: 12px; }

.filter-bar {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}

.level-btns { display: flex; gap: 4px; flex-wrap: wrap; }

.level-btn {
  padding: 3px 10px; border-radius: 99px; font-size: 11px; font-weight: 600;
  border: 1px solid var(--border); background: none; cursor: pointer;
  color: var(--text-muted); display: flex; align-items: center; gap: 4px;
  transition: background .1s, color .1s;
}
.level-btn:hover { background: var(--ks-50); color: var(--ks-700); }
.level-count { font-size: 10px; opacity: .7; }

.lvl-all.active      { background: #334155; color: #f1f5f9; border-color: #475569; }
.lvl-error.active    { background: #7f1d1d; color: #fca5a5; border-color: #991b1b; }
.lvl-critical.active { background: #450a0a; color: #fecaca; border-color: #7f1d1d; }
.lvl-warning.active  { background: #78350f; color: #fcd34d; border-color: #92400e; }
.lvl-info.active     { background: #1e3a5f; color: #93c5fd; border-color: #1e40af; }
.lvl-debug.active    { background: #1e293b; color: #94a3b8; border-color: #334155; }

.search-input { flex: 1; min-width: 200px; max-width: 320px; }

.auto-refresh-label {
  display: flex; align-items: center; gap: 5px;
  font-size: 12px; color: var(--text-muted); cursor: pointer; white-space: nowrap;
}
.auto-refresh-label input { accent-color: var(--ks-500); }

/* Terminal area */
.log-terminal {
  flex: 1; overflow-y: auto; min-height: 200px;
  background: #0f172a; border-radius: 10px;
  border: 1px solid #1e293b;
}

.log-table {
  width: 100%; border-collapse: collapse;
  font-family: ui-monospace, 'Cascadia Code', monospace; font-size: 11.5px;
}
.log-table thead { position: sticky; top: 0; background: #1e293b; z-index: 10; }
.log-table th {
  text-align: left; padding: 6px 10px; color: #64748b;
  font-size: 10px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase;
  border-bottom: 1px solid #334155;
}

.col-ts     { width: 160px; }
.col-level  { width: 86px; }
.col-logger { width: 180px; }
.col-msg    { }

.log-row { border-top: 1px solid rgba(51,65,85,.4); cursor: default; transition: background .1s; }
.log-row:hover { background: rgba(255,255,255,.03); }
.log-row.has-exc { cursor: pointer; }
.log-row.row-error    { background: rgba(127,29,29,.15); }
.log-row.row-critical { background: rgba(69,10,10,.25); }
.log-row.row-warning  { background: rgba(120,53,15,.12); }

.log-row td { padding: 4px 10px; vertical-align: top; }

.log-ts     { color: #475569; white-space: nowrap; }
.log-logger { color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px; }

.msg-error    { color: #fca5a5; }
.msg-critical { color: #fecaca; font-weight: 600; }
.msg-warning  { color: #fcd34d; }
.msg-info     { color: #e2e8f0; }
.msg-debug    { color: #64748b; }

.exc-hint { font-size: 10px; color: #64748b; margin-left: 6px; }

.exc-row td { padding: 4px 10px 8px; background: rgba(15,23,42,.8); }
.exc-pre {
  color: #f87171; font-size: 11px; white-space: pre-wrap; word-break: break-all;
  max-height: 200px; overflow-y: auto; margin: 0;
}

/* Level badges */
.level-badge {
  display: inline-block; padding: 1px 6px; border-radius: 4px;
  font-size: 10px; font-weight: 700; white-space: nowrap;
}
.badge-level-error    { background: #7f1d1d; color: #fca5a5; }
.badge-level-critical { background: #450a0a; color: #fecaca; }
.badge-level-warning  { background: #78350f; color: #fcd34d; }
.badge-level-info     { background: #1e3a5f; color: #93c5fd; }
.badge-level-debug    { background: #1e293b; color: #94a3b8; }

.log-empty {
  padding: 48px; text-align: center; color: #475569; font-family: inherit;
}

.log-footer {
  display: flex; align-items: center; gap: 16px;
  font-size: 11px; color: var(--text-muted); padding: 0 2px;
}
.footer-error { color: #f87171; font-weight: 600; }
.footer-warn  { color: #fbbf24; font-weight: 600; }
</style>

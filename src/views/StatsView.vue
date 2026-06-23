<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Monitoring &amp; Statistik</h1>
        <p>System-Ressourcen, rsyslog-Durchsatz, Prometheus &amp; Check_MK</p>
      </div>
      <div class="flex gap-2 items-center">
        <span class="text-muted text-sm">Auto-Refresh {{ autoRefresh ? 'an' : 'aus' }}</span>
        <label class="toggle-label">
          <input type="checkbox" v-model="autoRefresh" />
          <span class="toggle-track"><span class="toggle-thumb" /></span>
        </label>
        <button class="btn btn-ghost btn-sm" @click="load" :disabled="loading">Aktualisieren</button>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- ── Stat cards ─────────────────────────────────────────────────────── -->
    <div class="stats-grid mb-4">

      <!-- CPU -->
      <div class="metric-card">
        <div class="metric-header">
          <svg class="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
            <line x1="9" y1="2" x2="9" y2="4"/><line x1="15" y1="2" x2="15" y2="4"/>
            <line x1="9" y1="20" x2="9" y2="22"/><line x1="15" y1="20" x2="15" y2="22"/>
            <line x1="2" y1="9" x2="4" y2="9"/><line x1="2" y1="15" x2="4" y2="15"/>
            <line x1="20" y1="9" x2="22" y2="9"/><line x1="20" y1="15" x2="22" y2="15"/>
          </svg>
          <span class="metric-title">CPU</span>
          <span class="metric-value" :class="severityClass(stats?.cpu?.percent, 80, 95)">
            {{ stats?.cpu?.percent >= 0 ? stats.cpu.percent + '%' : '—' }}
          </span>
        </div>
        <div class="gauge-bar">
          <div class="gauge-fill" :class="severityClass(stats?.cpu?.percent, 80, 95)"
               :style="{ width: clamp(stats?.cpu?.percent) + '%' }"></div>
        </div>
        <div class="metric-sub">
          Load: {{ stats?.cpu?.load_1 ?? '—' }} / {{ stats?.cpu?.load_5 ?? '—' }} / {{ stats?.cpu?.load_15 ?? '—' }}
          <span class="text-muted">(1/5/15 min)</span>
        </div>
      </div>

      <!-- RAM -->
      <div class="metric-card">
        <div class="metric-header">
          <svg class="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6l3-3h12l3 3v12l-3 3H6l-3-3V6z"/>
            <line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/>
            <line x1="12" y1="3" x2="12" y2="21"/>
          </svg>
          <span class="metric-title">RAM</span>
          <span class="metric-value" :class="severityClass(stats?.memory?.percent, 85, 95)">
            {{ stats?.memory?.percent >= 0 ? stats.memory.percent + '%' : '—' }}
          </span>
        </div>
        <div class="gauge-bar">
          <div class="gauge-fill" :class="severityClass(stats?.memory?.percent, 85, 95)"
               :style="{ width: clamp(stats?.memory?.percent) + '%' }"></div>
        </div>
        <div class="metric-sub">
          {{ stats?.memory?.used_mb ?? '—' }} MB / {{ stats?.memory?.total_mb ?? '—' }} MB
          <span class="text-muted">({{ stats?.memory?.avail_mb ?? '—' }} MB frei)</span>
        </div>
      </div>

      <!-- Disk / -->
      <div class="metric-card">
        <div class="metric-header">
          <svg class="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          </svg>
          <span class="metric-title">Disk <code class="metric-path">/</code></span>
          <span class="metric-value" :class="severityClass(stats?.disk_root?.percent, 80, 90)">
            {{ stats?.disk_root?.percent >= 0 ? stats.disk_root.percent + '%' : '—' }}
          </span>
        </div>
        <div class="gauge-bar">
          <div class="gauge-fill" :class="severityClass(stats?.disk_root?.percent, 80, 90)"
               :style="{ width: clamp(stats?.disk_root?.percent) + '%' }"></div>
        </div>
        <div class="metric-sub">
          {{ stats?.disk_root?.used_gb ?? '—' }} GB / {{ stats?.disk_root?.total_gb ?? '—' }} GB
        </div>
      </div>

      <!-- Disk /data/syslog -->
      <div class="metric-card">
        <div class="metric-header">
          <svg class="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          </svg>
          <span class="metric-title">Disk <code class="metric-path">/data/syslog</code></span>
          <span class="metric-value" :class="severityClass(stats?.disk_syslog?.percent, 80, 90)">
            {{ stats?.disk_syslog?.percent >= 0 ? stats.disk_syslog.percent + '%' : '—' }}
          </span>
        </div>
        <div class="gauge-bar">
          <div class="gauge-fill" :class="severityClass(stats?.disk_syslog?.percent, 80, 90)"
               :style="{ width: clamp(stats?.disk_syslog?.percent) + '%' }"></div>
        </div>
        <div class="metric-sub">
          {{ stats?.disk_syslog?.used_gb ?? '—' }} GB / {{ stats?.disk_syslog?.total_gb ?? '—' }} GB
        </div>
      </div>

      <!-- Events/sec -->
      <div class="metric-card">
        <div class="metric-header">
          <svg class="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          <span class="metric-title">Events/sec</span>
          <span class="metric-value" style="color:var(--ks-600);">
            {{ stats?.rsyslog?.events_per_sec ?? '—' }}
          </span>
        </div>
        <div class="metric-sub">
          Geschätzt aus Logfile-Deltazählung
          <span class="text-muted">(zweites Sample nötig)</span>
        </div>
        <div v-if="stats?.rsyslog?.queue_size != null" class="metric-sub" style="margin-top:4px;">
          Queue: {{ stats.rsyslog.queue_size }} | Dropped: {{ stats.rsyslog.dropped ?? 0 }}
        </div>
      </div>

    </div>

    <!-- ── Heartbeat ──────────────────────────────────────────────────────── -->
    <div class="card mb-4">
      <div class="card-header">
        <span>Host-Heartbeat</span>
        <span class="text-muted text-sm">Letzter Log-Eingang pro Host</span>
      </div>
      <div v-if="!heartbeat.length" class="card-body text-muted" style="font-size:13px;">
        Keine Hosts / kein /data/syslog auf diesem System.
      </div>
      <div v-else class="hb-table">
        <div class="hb-row hb-head">
          <span>Host</span><span>Zuletzt gesehen</span><span>Vor</span><span>Status</span>
        </div>
        <div v-for="h in heartbeat" :key="h.host" class="hb-row" :class="'hb-'+h.status">
          <span class="font-mono hb-host">{{ h.host }}</span>
          <span class="text-muted hb-ts" style="font-size:12px;">{{ h.last_seen ? formatDate(h.last_seen) : '—' }}</span>
          <span class="hb-age" style="font-size:12px;">{{ h.age_seconds != null ? formatAge(h.age_seconds) : '—' }}</span>
          <span class="hb-badge" :class="'badge-hb-'+h.status">
            {{ h.status === 'ok' ? 'OK' : h.status === 'warn' ? 'Warnung' : h.status === 'crit' ? 'Kritisch' : 'Unbekannt' }}
          </span>
        </div>
      </div>
    </div>

    <!-- ── Anomalie-Meldungen ──────────────────────────────────────────────── -->
    <div v-if="anomalies.length" class="anomaly-banner mb-4">
      <div class="anomaly-icon">⚠</div>
      <div class="anomaly-text">
        <strong>Anomalie erkannt:</strong>
        <span v-for="(a, i) in anomalies" :key="a.host">
          {{ i > 0 ? ', ' : '' }}
          <b>{{ a.host }}</b> — {{ a.current_count }} Events/h ({{ a.factor }}× Durchschnitt)
        </span>
        <span v-if="anomalyEmailSent" class="text-muted" style="font-size:12px;"> — Alert-E-Mail versendet</span>
      </div>
    </div>

    <!-- ── Event-Rate Histogram ───────────────────────────────────────────── -->
    <div class="card mb-4">
      <div class="card-header">
        <span>Event-Rate pro Host</span>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-ghost btn-sm"
            :class="{ 'btn-active': rateView === 'hourly' }" @click="rateView='hourly'">24h (stündlich)</button>
          <button class="btn btn-ghost btn-sm"
            :class="{ 'btn-active': rateView === 'daily' }" @click="rateView='daily'">14 Tage</button>
        </div>
      </div>
      <div v-if="!eventRate.length" class="card-body text-muted" style="font-size:13px;">
        Keine Log-Daten verfügbar.
      </div>
      <div v-else class="card-body rate-container">
        <div v-for="row in eventRate" :key="row.host" class="rate-host">
          <div class="rate-host-label font-mono">{{ row.host }}</div>
          <div class="rate-bars">
            <div v-for="(cnt, idx) in (rateView === 'hourly' ? row.hourly : row.daily)"
                 :key="idx"
                 class="rate-bar-wrap"
                 :title="rateView === 'hourly' ? `vor ${idx}h: ${cnt}` : `vor ${idx}d: ${cnt}`">
              <div class="rate-bar"
                   :class="isAnomaly(row.host, idx) ? 'rate-bar-anomaly' : ''"
                   :style="{ height: barHeight(cnt, maxCount(rateView === 'hourly' ? row.hourly : row.daily)) + '%' }">
              </div>
              <div v-if="rateView === 'hourly' && (idx % 6 === 0)" class="rate-label">{{ idx }}h</div>
              <div v-else-if="rateView === 'daily'" class="rate-label">-{{ idx }}d</div>
            </div>
          </div>
          <div class="rate-summary">
            Gesamt {{ rateView === 'hourly' ? '24h' : '14d' }}:
            <b>{{ (rateView === 'hourly' ? row.hourly : row.daily).reduce((a:number,b:number)=>a+b,0).toLocaleString('de-DE') }}</b>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Integrations ───────────────────────────────────────────────────── -->
    <div class="grid-cols-2">

      <!-- Prometheus -->
      <div class="card">
        <div class="card-header">
          <span>Prometheus</span>
          <span class="badge badge-gray">optional</span>
        </div>
        <div class="card-body">
          <p class="text-muted text-sm" style="margin-bottom:12px;">
            Metriken im Prometheus text-Format. Direkt als Scrape-Target oder über einen Exporter nutzbar.
          </p>
          <div class="integration-endpoint">
            <code>GET /api/metrics</code>
            <button class="btn btn-ghost btn-sm" @click="copyUrl('/api/metrics')">Kopieren</button>
            <a :href="metricsUrl" target="_blank" class="btn btn-ghost btn-sm">Öffnen ↗</a>
          </div>
          <details style="margin-top:12px;">
            <summary class="text-sm" style="cursor:pointer;color:var(--ks-600);">Prometheus scrape_config anzeigen</summary>
            <pre class="snippet-box">{{ promConfig }}</pre>
            <button class="btn btn-ghost btn-sm" style="margin-top:4px;" @click="copy(promConfig)">📋 Kopieren</button>
          </details>
        </div>
      </div>

      <!-- Check_MK -->
      <div class="card">
        <div class="card-header">
          <span>Check_MK</span>
          <span class="badge badge-blue">primäres Monitoring</span>
        </div>
        <div class="card-body">
          <p class="text-muted text-sm" style="margin-bottom:12px;">
            Ausgabe im Check_MK Local-Check-Format. Als Local-Check-Script auf dem Monitoring-Host einbinden.
          </p>
          <div class="integration-endpoint">
            <code>GET /api/checkmk</code>
            <button class="btn btn-ghost btn-sm" @click="copyUrl('/api/checkmk')">Kopieren</button>
            <a :href="checkmkUrl" target="_blank" class="btn btn-ghost btn-sm">Öffnen ↗</a>
          </div>
          <details style="margin-top:12px;">
            <summary class="text-sm" style="cursor:pointer;color:var(--ks-600);">Local-Check-Script anzeigen</summary>
            <pre class="snippet-box">{{ checkmkScript }}</pre>
            <button class="btn btn-ghost btn-sm" style="margin-top:4px;" @click="copy(checkmkScript)">📋 Kopieren</button>
          </details>
        </div>
      </div>

    </div>

    <!-- Live-Vorschau Check_MK Output -->
    <div class="card" style="margin-top:16px;">
      <div class="card-header">
        <span>Check_MK Live-Output</span>
        <span class="text-muted text-sm">{{ lastRefresh }}</span>
      </div>
      <div class="card-body" style="padding:0;">
        <pre v-if="checkmkLive" class="checkmk-output">{{ checkmkLive }}</pre>
        <div v-else class="text-muted" style="padding:16px;font-size:13px;">Wird geladen …</div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

const auth      = useAuthStore();
const stats     = ref<Record<string, any> | null>(null);
const checkmkLive = ref('');
const loading   = ref(false);
const error     = ref('');
const autoRefresh = ref(true);
const lastRefresh = ref('');

interface HbHost { host: string; last_seen: string | null; age_seconds: number | null; status: string; }
interface EventRateRow { host: string; hourly: number[]; daily: number[]; }
interface Anomaly { host: string; current_count: number; rolling_avg: number; factor: number; }

const heartbeat  = ref<HbHost[]>([]);
const eventRateData = ref<EventRateRow[]>([]);
const anomalies  = ref<Anomaly[]>([]);
const anomalyEmailSent = ref(false);
const rateView   = ref<'hourly' | 'daily'>('hourly');
const eventRate  = computed(() => eventRateData.value);

let timer: ReturnType<typeof setInterval> | null = null;

const metricsUrl  = computed(() => `${window.location.origin}/api/metrics`);
const checkmkUrl  = computed(() => `${window.location.origin}/api/checkmk`);

const promConfig = computed(() => {
  const host = window.location.host;
  return `scrape_configs:
  - job_name: rsyslog_manager
    metrics_path: /api/metrics
    scheme: https
    static_configs:
      - targets: ['${host}']
    # Bei JWT-Auth Bearer-Token als Header:
    authorization:
      type: Bearer
      credentials: <your-token>`;
});

const checkmkScript = `#!/bin/bash
# Pfad: /usr/lib/check_mk_agent/local/rsyslog_manager
# Voraussetzung: curl, jq
TOKEN="<bearer-token>"
HOST="https://${window.location.host}"
curl -sf -H "Authorization: Bearer $TOKEN" "$HOST/api/checkmk"`;

async function load() {
  loading.value = true;
  error.value   = '';
  try {
    await auth.initialize();
    const [sRes, cRes, hbRes, erRes] = await Promise.all([
      apiClient.get('/stats'),
      apiClient.get('/checkmk', { responseType: 'text' }),
      apiClient.get('/rsyslog/heartbeat').catch(() => ({ data: { hosts: [] } })),
      apiClient.get('/rsyslog/event-rate').catch(() => ({ data: { hourly: [], daily: [], anomalies: [] } })),
    ]);
    stats.value       = sRes.data;
    checkmkLive.value = typeof cRes.data === 'string' ? cRes.data : JSON.stringify(cRes.data);
    heartbeat.value   = hbRes.data.hosts ?? [];
    anomalies.value   = erRes.data.anomalies ?? [];

    // Merge hourly + daily into single rows per host
    const hourlyMap: Record<string, number[]> = {};
    const dailyMap:  Record<string, number[]> = {};
    for (const row of (erRes.data.hourly ?? [])) hourlyMap[row.host] = row.counts;
    for (const row of (erRes.data.daily  ?? [])) dailyMap[row.host]  = row.counts;
    const allHosts = [...new Set([...Object.keys(hourlyMap), ...Object.keys(dailyMap)])];
    eventRateData.value = allHosts.map(h => ({
      host:   h,
      hourly: hourlyMap[h] ?? Array(24).fill(0),
      daily:  dailyMap[h]  ?? Array(14).fill(0),
    }));

    lastRefresh.value = new Date().toLocaleTimeString('de-DE');
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Statistik konnte nicht geladen werden.';
  } finally {
    loading.value = false;
  }
}

function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }); }
  catch { return iso; }
}
function formatAge(s: number): string {
  if (s < 60)   return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}min`;
  if (s < 86400) return `${Math.floor(s / 3600)}h`;
  return `${Math.floor(s / 86400)}d`;
}
function barHeight(cnt: number, maxCnt: number): number {
  return maxCnt > 0 ? Math.max(2, Math.round((cnt / maxCnt) * 100)) : 2;
}
function maxCount(arr: number[]): number {
  return Math.max(...arr, 1);
}
function isAnomaly(host: string, idx: number): boolean {
  return idx === 0 && anomalies.value.some(a => a.host === host);
}

function clamp(v: number | undefined): number {
  if (v == null || v < 0) return 0;
  return Math.min(100, Math.max(0, v));
}

function severityClass(v: number | undefined, warn: number, crit: number): string {
  if (v == null || v < 0) return 'metric-unknown';
  if (v >= crit) return 'metric-crit';
  if (v >= warn) return 'metric-warn';
  return 'metric-ok';
}

async function copyUrl(path: string) {
  await copy(`${window.location.origin}${path}`);
}
async function copy(text: string) {
  try { await navigator.clipboard.writeText(text); } catch { /* ignore */ }
}

onMounted(async () => {
  await load();
  timer = setInterval(() => { if (autoRefresh.value) load(); }, 10_000);
});
onUnmounted(() => { if (timer) clearInterval(timer); });
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.text-sm { font-size: 12px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.metric-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.metric-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.metric-icon {
  width: 18px; height: 18px;
  flex-shrink: 0;
  stroke: var(--text-muted);
}
.metric-title {
  flex: 1;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: .04em;
  display: flex; align-items: center; gap: 4px;
}
.metric-path {
  font-size: 10px;
  font-family: ui-monospace, monospace;
  background: var(--ks-100);
  padding: 0 4px;
  border-radius: 3px;
  color: var(--ks-700);
}
.metric-value {
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.metric-ok      { color: #16a34a; }
.metric-warn    { color: #d97706; }
.metric-crit    { color: #dc2626; }
.metric-unknown { color: var(--text-muted); }

.gauge-bar {
  height: 6px;
  background: var(--border);
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 8px;
}
.gauge-fill {
  height: 100%;
  border-radius: 99px;
  transition: width .5s ease;
}
.gauge-fill.metric-ok   { background: #22c55e; }
.gauge-fill.metric-warn { background: #f59e0b; }
.gauge-fill.metric-crit { background: #ef4444; }
.gauge-fill.metric-unknown { background: var(--border); }

.metric-sub {
  font-size: 11px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.grid-cols-2 {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.integration-endpoint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--ks-50);
  border: 1px solid var(--ks-200);
  border-radius: 6px;
  font-size: 12px;
}
.integration-endpoint code {
  font-family: ui-monospace, monospace;
  flex: 1;
  color: var(--ks-700);
}

.snippet-box {
  margin-top: 8px;
  padding: 10px 14px;
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 6px;
  font-size: 11px;
  font-family: ui-monospace, monospace;
  white-space: pre;
  overflow-x: auto;
}

.checkmk-output {
  padding: 12px 16px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  white-space: pre;
  overflow-x: auto;
  background: #0f172a;
  color: #94a3b8;
  border-radius: 0 0 10px 10px;
  line-height: 1.7;
}

/* Heartbeat table */
.hb-table { font-size: 13px; }
.hb-row   { display: grid; grid-template-columns: 1fr 160px 80px 90px; gap: 8px;
  padding: 8px 16px; border-bottom: 1px solid var(--border-soft); align-items: center; }
.hb-head  { font-size: 11px; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .05em; background: var(--ks-50); }
.hb-ok   { }
.hb-warn { background: #fffbeb; }
.hb-crit { background: #fef2f2; }
.hb-unknown { background: var(--bg); }
.hb-host { font-family: ui-monospace, monospace; }
.badge-hb-ok      { background: #dcfce7; color: #166534; font-size: 11px; font-weight: 700;
  padding: 2px 8px; border-radius: 9px; }
.badge-hb-warn    { background: #fef9c3; color: #78350f; font-size: 11px; font-weight: 700;
  padding: 2px 8px; border-radius: 9px; }
.badge-hb-crit    { background: #fecaca; color: #991b1b; font-size: 11px; font-weight: 700;
  padding: 2px 8px; border-radius: 9px; }
.badge-hb-unknown { background: #f1f5f9; color: #64748b; font-size: 11px; font-weight: 700;
  padding: 2px 8px; border-radius: 9px; }

/* Anomaly banner */
.anomaly-banner { display: flex; align-items: center; gap: 12px; padding: 12px 16px;
  background: #fffbeb; border: 1.5px solid #f59e0b; border-radius: 8px; font-size: 13px; }
.anomaly-icon { font-size: 20px; flex-shrink: 0; }
.anomaly-text { flex: 1; }

/* Event-rate histogram */
.rate-container { display: flex; flex-direction: column; gap: 20px; }
.rate-host { }
.rate-host-label { font-size: 12px; font-family: ui-monospace, monospace;
  color: var(--ks-600); font-weight: 600; margin-bottom: 4px; }
.rate-bars { display: flex; gap: 3px; align-items: flex-end; height: 64px;
  border-bottom: 1px solid var(--border-soft); padding-bottom: 2px; }
.rate-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: flex-end; height: 100%; cursor: default; }
.rate-bar { width: 100%; background: var(--ks-300); border-radius: 2px 2px 0 0;
  min-height: 2px; transition: height .3s ease; }
.rate-bar:hover { background: var(--ks-500); }
.rate-bar-anomaly { background: #ef4444 !important; }
.rate-label { font-size: 9px; color: var(--text-muted); margin-top: 2px; white-space: nowrap; }
.rate-summary { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.btn-active { background: var(--ks-100) !important; color: var(--ks-700) !important; font-weight: 600; }

/* Toggle */
.toggle-label { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; }
.toggle-label input { display: none; }
.toggle-track {
  position: relative; display: inline-block; width: 32px; height: 18px;
  background: #cbd5e1; border-radius: 999px; transition: background .2s; flex-shrink: 0;
}
.toggle-label input:checked + .toggle-track { background: var(--ks-500); }
.toggle-thumb {
  position: absolute; top: 2px; left: 2px; width: 14px; height: 14px;
  background: #fff; border-radius: 50%; transition: left .2s; box-shadow: 0 1px 2px rgba(0,0,0,.2);
}
.toggle-label input:checked + .toggle-track .toggle-thumb { left: 16px; }
</style>

<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Meine Hosts</h1>
        <p>Übersicht der Dir zugewiesenen Hosts</p>
      </div>
      <div class="flex gap-2 items-center">
        <label class="toggle-label">
          <input type="checkbox" v-model="autoRefresh" />
          <span class="toggle-track"><span class="toggle-thumb" /></span>
        </label>
        <span class="text-muted text-sm">Auto-Refresh</span>
        <button class="btn btn-ghost btn-sm" @click="load" :disabled="loading">Aktualisieren</button>
      </div>
    </div>

    <div v-if="loading && !hosts.length" class="text-muted" style="padding:32px;text-align:center;font-size:13px;">
      Wird geladen…
    </div>

    <!-- Maintenance banner -->
    <div v-if="maintenanceActive" class="maint-banner mb-4">
      <span style="font-size:18px;">🔧</span>
      <span>Wartungsmodus aktiv — Alert-Emails werden zurückgehalten.</span>
    </div>

    <!-- No hosts assigned -->
    <div v-else-if="!loading && !hosts.length" class="card">
      <div class="card-body text-muted" style="padding:32px;text-align:center;font-size:13px;">
        <div v-if="isUnrestricted">Alle Hosts werden angezeigt — aber kein Log-Verzeichnis gefunden.</div>
        <div v-else>Kein Host zugewiesen. Ein Administrator kann Dir Hosts zuweisen.</div>
      </div>
    </div>

    <!-- Host cards grid -->
    <div v-else class="host-grid">
      <div v-for="h in hosts" :key="h.host" class="host-card card"
           :class="'hc-' + h.status">

        <!-- Card header -->
        <div class="hc-header">
          <div class="hc-name font-mono">{{ h.host }}</div>
          <div class="hc-badge" :class="'badge-hb-' + h.status">
            {{ statusLabel(h.status) }}
          </div>
        </div>

        <!-- Last seen -->
        <div class="hc-section">
          <div class="hc-section-label">Letzter Eingang</div>
          <div class="hc-value" :class="h.status !== 'ok' ? 'hc-warn-text' : ''">
            {{ h.last_seen ? formatDate(h.last_seen) : '—' }}
          </div>
          <div v-if="h.age_seconds != null" class="hc-sub">
            vor {{ formatAge(h.age_seconds) }}
          </div>
        </div>

        <!-- Event rate (last 24h) -->
        <div class="hc-section">
          <div class="hc-section-label">Events letzte 24h</div>
          <div class="hc-value">{{ h.events24h.toLocaleString('de-DE') }}</div>
          <div class="hc-mini-chart">
            <div v-for="(cnt, idx) in h.hourly" :key="idx" class="hc-bar-wrap">
              <div class="hc-bar"
                   :class="idx === 0 && h.anomaly ? 'hc-bar-anomaly' : ''"
                   :style="{ height: barHeight(cnt, h.maxHourly) + '%' }"
                   :title="`vor ${idx}h: ${cnt}`">
              </div>
            </div>
          </div>
          <div v-if="h.anomaly" class="hc-anomaly-tag">
            ⚠ Anomalie: {{ h.anomaly.current_count }} Events/h ({{ h.anomaly.factor }}×)
          </div>
        </div>

        <!-- Quick links -->
        <div class="hc-footer">
          <router-link :to="{ name: 'Logs', query: { host: h.host } }" class="btn btn-ghost btn-sm">
            Logs →
          </router-link>
          <router-link :to="{ name: 'LogFiles' }" class="btn btn-ghost btn-sm">
            Dateien →
          </router-link>
        </div>
      </div>
    </div>

    <div v-if="lastRefresh" class="text-muted text-sm" style="text-align:right;margin-top:8px;">
      Zuletzt aktualisiert: {{ lastRefresh }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

interface HostCard {
  host: string;
  status: string;
  last_seen: string | null;
  age_seconds: number | null;
  hourly: number[];
  events24h: number;
  maxHourly: number;
  anomaly: { current_count: number; rolling_avg: number; factor: number } | null;
}

const auth        = useAuthStore();
const loading     = ref(false);
const autoRefresh = ref(true);
const lastRefresh = ref('');
const hosts       = ref<HostCard[]>([]);
const maintenanceActive = ref(false);
const isUnrestricted    = ref(false);

let timer: ReturnType<typeof setInterval> | null = null;

async function load() {
  loading.value = true;
  try {
    await auth.initialize();
    const [hbRes, erRes, maintRes] = await Promise.all([
      apiClient.get('/rsyslog/heartbeat'),
      apiClient.get('/rsyslog/event-rate'),
      apiClient.get('/settings/maintenance/active').catch(() => ({ data: { active: false } })),
    ]);

    maintenanceActive.value = maintRes.data.active ?? false;

    const hbHosts: Map<string, any> = new Map(
      (hbRes.data.hosts ?? []).map((h: any) => [h.host, h])
    );
    const hourlyMap: Map<string, number[]> = new Map(
      (erRes.data.hourly ?? []).map((r: any) => [r.host, r.counts])
    );
    const anomalyMap: Map<string, any> = new Map(
      (erRes.data.anomalies ?? []).map((a: any) => [a.host, a])
    );

    // Merge heartbeat + event-rate data
    const allHostNames = new Set([...hbHosts.keys(), ...hourlyMap.keys()]);
    isUnrestricted.value = hbRes.data.hosts?.length === 0;

    hosts.value = [...allHostNames].sort().map(host => {
      const hb      = hbHosts.get(host) ?? { status: 'unknown', last_seen: null, age_seconds: null };
      const hourly  = hourlyMap.get(host) ?? Array(24).fill(0);
      const events24h = hourly.reduce((a: number, b: number) => a + b, 0);
      const maxH    = Math.max(...hourly, 1);
      return {
        host,
        status:      hb.status,
        last_seen:   hb.last_seen,
        age_seconds: hb.age_seconds,
        hourly,
        events24h,
        maxHourly:   maxH,
        anomaly:     anomalyMap.get(host) ?? null,
      };
    });

    lastRefresh.value = new Date().toLocaleTimeString('de-DE');
  } catch { /* ignore */ }
  finally { loading.value = false; }
}

function statusLabel(s: string): string {
  return s === 'ok' ? 'OK' : s === 'warn' ? 'Warnung' : s === 'crit' ? 'Kritisch' : 'Unbekannt';
}
function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }); }
  catch { return iso; }
}
function formatAge(s: number): string {
  if (s < 60)    return `${s}s`;
  if (s < 3600)  return `${Math.floor(s / 60)}min`;
  if (s < 86400) return `${Math.floor(s / 3600)}h`;
  return `${Math.floor(s / 86400)}d`;
}
function barHeight(cnt: number, maxCnt: number): number {
  return maxCnt > 0 ? Math.max(3, Math.round((cnt / maxCnt) * 100)) : 3;
}

onMounted(async () => {
  await load();
  timer = setInterval(() => { if (autoRefresh.value) load(); }, 30_000);
});
onUnmounted(() => { if (timer) clearInterval(timer); });
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.text-sm { font-size: 12px; }
.font-mono { font-family: ui-monospace, monospace; }

/* Maintenance banner */
.maint-banner { display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  background: #fef9c3; border: 1.5px solid #f59e0b; border-radius: 8px; font-size: 13px; }

/* Host card grid */
.host-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }

.host-card { padding: 0; transition: box-shadow .2s; }
.host-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.1); }
.hc-ok   { border-left: 3px solid #22c55e; }
.hc-warn { border-left: 3px solid #f59e0b; }
.hc-crit { border-left: 3px solid #ef4444; }
.hc-unknown { border-left: 3px solid #94a3b8; }

.hc-header { display: flex; justify-content: space-between; align-items: center;
  padding: 12px 14px; border-bottom: 1px solid var(--border-soft); }
.hc-name { font-size: 14px; font-weight: 600; }

.hc-section { padding: 10px 14px; border-bottom: 1px solid var(--border-soft); }
.hc-section-label { font-size: 10px; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .05em; margin-bottom: 3px; }
.hc-value { font-size: 14px; font-weight: 500; }
.hc-warn-text { color: #b45309; }
.hc-sub { font-size: 11px; color: var(--text-muted); }

/* Mini sparkline chart */
.hc-mini-chart { display: flex; gap: 2px; align-items: flex-end; height: 32px;
  margin-top: 6px; border-bottom: 1px solid var(--border-soft); padding-bottom: 2px; }
.hc-bar-wrap { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; height: 100%; }
.hc-bar { width: 100%; background: var(--ks-200); border-radius: 1px 1px 0 0; min-height: 2px; }
.hc-bar-anomaly { background: #ef4444 !important; }

.hc-anomaly-tag { font-size: 11px; color: #b91c1c; font-weight: 600; margin-top: 4px; }

.hc-footer { display: flex; gap: 8px; padding: 8px 10px; }

/* Status badges */
.badge-hb-ok      { background: #dcfce7; color: #166534; font-size: 10px; font-weight: 700;
  padding: 2px 8px; border-radius: 9px; }
.badge-hb-warn    { background: #fef9c3; color: #78350f; font-size: 10px; font-weight: 700;
  padding: 2px 8px; border-radius: 9px; }
.badge-hb-crit    { background: #fecaca; color: #991b1b; font-size: 10px; font-weight: 700;
  padding: 2px 8px; border-radius: 9px; }
.badge-hb-unknown { background: #f1f5f9; color: #64748b; font-size: 10px; font-weight: 700;
  padding: 2px 8px; border-radius: 9px; }

/* Toggle */
.toggle-label { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; }
.toggle-label input { display: none; }
.toggle-track { position: relative; display: inline-block; width: 32px; height: 18px;
  background: #cbd5e1; border-radius: 999px; transition: background .2s; }
.toggle-label input:checked + .toggle-track { background: var(--ks-500); }
.toggle-thumb { position: absolute; top: 2px; left: 2px; width: 14px; height: 14px;
  background: #fff; border-radius: 50%; transition: left .2s; }
.toggle-label input:checked + .toggle-track .toggle-thumb { left: 16px; }
</style>

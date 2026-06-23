<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Dashboard</h1>
        <p>rsyslog Dienst-Status und Schnellzugriff</p>
      </div>
    </div>

    <!-- Stat cards -->
    <div class="grid-cols-4 mb-5">
      <div class="stat-card">
        <div class="stat-icon" :class="status?.status === 'running' ? 'stat-green' : 'stat-yellow'">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
        <div>
          <div class="stat-value" :style="status?.status === 'running' ? 'color:#16a34a' : 'color:#ca8a04'">
            {{ status?.status ?? '—' }}
          </div>
          <div class="stat-label">Service-Status</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-blue">
          <svg viewBox="0 0 24 24"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        </div>
        <div>
          <div class="stat-value" style="font-size:15px;color:var(--ks-600)">{{ status?.uptime ?? '—' }}</div>
          <div class="stat-label">Uptime</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" :class="config?.editable ? 'stat-green' : 'stat-gray'">
          <svg viewBox="0 0 24 24"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        </div>
        <div>
          <div class="stat-value" style="font-size:15px;" :style="config?.editable ? 'color:#16a34a' : 'color:#475569'">
            {{ config?.editable ? 'Ja' : 'Nein' }}
          </div>
          <div class="stat-label">Konfiguration editierbar</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-blue">
          <svg viewBox="0 0 24 24"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
        </div>
        <div>
          <div class="stat-value" style="font-size:15px;color:var(--ks-600)">{{ auth.user?.role ?? '—' }}</div>
          <div class="stat-label">Ihre Rolle</div>
        </div>
      </div>
    </div>

    <!-- Quick actions + info -->
    <div class="grid-cols-auto">

      <!-- Service actions -->
      <div class="card">
        <div class="card-header">Service-Management</div>
        <div class="card-body">
          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">Version</span>
              <span class="meta-value">{{ status?.version ?? '—' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">SubState</span>
              <span class="meta-value">{{ status?.sub_state ?? '—' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">PID</span>
              <span class="meta-value font-mono">{{ status?.main_pid && status.main_pid !== '0' ? status.main_pid : '—' }}</span>
            </div>
          </div>
          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">Neustarts</span>
              <span :class="['meta-value', nrestarts > 0 ? 'restart-warn' : '']">
                {{ nrestarts }}
                <span v-if="nrestarts > 0" class="restart-badge">!</span>
              </span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Exit-Status</span>
              <span :class="['meta-value font-mono', status?.exec_status && status.exec_status !== '0' ? 'restart-warn' : '']">
                {{ status?.exec_status ?? '—' }}
              </span>
            </div>
          </div>
          <div class="action-row">
            <button class="btn btn-primary" @click="reloadConfig" :disabled="!canReload || reloading">
              {{ reloading ? 'Lädt …' : 'Konfiguration neu laden' }}
            </button>
          </div>
          <p v-if="reloadMsg" class="text-muted text-sm" style="margin-top:8px;">{{ reloadMsg }}</p>
        </div>
      </div>

      <!-- Config info -->
      <div class="card">
        <div class="card-header">
          Konfiguration
          <router-link to="/config" style="font-size:12px;color:var(--ks-500);text-decoration:none;font-weight:400;">Öffnen →</router-link>
        </div>
        <div class="card-body">
          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">Pfad</span>
              <span class="meta-value font-mono" style="font-size:12px;">{{ config?.config_path ?? '—' }}</span>
            </div>
          </div>
          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">Letzte Änderung</span>
              <span class="meta-value">{{ config?.last_modified ?? '—' }}</span>
            </div>
          </div>
          <p class="text-muted text-sm">{{ config?.summary }}</p>
        </div>
      </div>

      <!-- Log viewer link -->
      <div class="card">
        <div class="card-header">
          Log-Analyse
          <router-link to="/logs" style="font-size:12px;color:var(--ks-500);text-decoration:none;font-weight:400;">Öffnen →</router-link>
        </div>
        <div class="card-body">
          <p class="text-muted" style="font-size:13px;margin-bottom:12px;">Live-Logs, Filter und Analyse der rsyslog-Ausgabe.</p>
          <button class="btn btn-ghost btn-sm" @click="$router.push({ name: 'Logs' })">Logs anzeigen</button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

const auth    = useAuthStore();
const router  = useRouter();
const status  = ref<Record<string, string> | null>(null);
const config  = ref<Record<string, string | boolean> | null>(null);
const reloading  = ref(false);
const reloadMsg  = ref('');

const canReload  = computed(() => auth.isAdmin || auth.isOperator);
const nrestarts  = computed(() => parseInt(String(status.value?.n_restarts ?? '0'), 10) || 0);;

async function fetchDashboardData() {
  try {
    await auth.initialize();
    const [s, c] = await Promise.all([
      apiClient.get('/rsyslog/status'),
      apiClient.get('/rsyslog/config'),
    ]);
    status.value = s.data;
    config.value = c.data;
  } catch {
    // errors shown individually below
  }
}

async function reloadConfig() {
  reloading.value = true;
  reloadMsg.value = '';
  try {
    await apiClient.post('/rsyslog/reload');
    reloadMsg.value = 'Konfiguration erfolgreich neu geladen.';
    await fetchDashboardData();
  } catch (e: any) {
    reloadMsg.value = e.response?.data?.detail ?? 'Fehler beim Reload.';
  } finally {
    reloading.value = false;
  }
}

onMounted(fetchDashboardData);
</script>

<style scoped>
.font-mono   { font-family: ui-monospace, monospace; }
.restart-warn { color: #b91c1c; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.restart-badge { background: #fecaca; color: #991b1b; font-size: 11px; font-weight: 700;
  padding: 0 5px; border-radius: 9px; }
</style>

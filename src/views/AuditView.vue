<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Audit-Log</h1>
        <p>Wer hat wann was geändert</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-ghost btn-sm" @click="load" :disabled="loading">Aktualisieren</button>
        <button class="btn btn-danger btn-sm" @click="clearLog" :disabled="loading">Log leeren</button>
      </div>
    </div>

    <div v-if="message" :class="['alert', msgType === 'error' ? 'alert-error' : 'alert-success']">
      {{ message }}
    </div>

    <!-- Filter -->
    <div class="card mb-4 filter-bar">
      <div class="filter-row">
        <div class="filter-group" style="flex:2;">
          <label class="filter-label">Benutzer</label>
          <input class="input input-sm" v-model="filterUser" placeholder="admin …" @input="applyFilter" />
        </div>
        <div class="filter-group" style="flex:2;">
          <label class="filter-label">Aktion</label>
          <input class="input input-sm" v-model="filterAction" placeholder="config.update …" @input="applyFilter" />
        </div>
        <div class="filter-group" style="flex:3;">
          <label class="filter-label">Detail / Suche</label>
          <input class="input input-sm" v-model="filterDetail" placeholder="Freitext …" @input="applyFilter" />
        </div>
        <div class="filter-group" style="min-width:80px;">
          <label class="filter-label">Limit</label>
          <input type="number" class="input input-sm" v-model.number="limitVal"
                 min="10" max="2000" @change="load" style="width:70px;" />
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="card">
      <div class="card-header">
        <span>Einträge</span>
        <span class="text-muted text-sm">
          {{ filtered.length }} angezeigt{{ filtered.length !== entries.length ? ` (von ${entries.length} geladen)` : '' }}
        </span>
      </div>
      <div class="audit-table-wrap">
        <table class="data-table audit-table" v-if="filtered.length">
          <thead>
            <tr>
              <th style="width:160px;">Zeitstempel</th>
              <th style="width:100px;">Benutzer</th>
              <th style="width:180px;">Aktion</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(e, i) in filtered" :key="i" :class="actionRowClass(e.action)">
              <td class="ts-cell">{{ formatTs(e.ts) }}</td>
              <td>
                <span class="badge badge-blue" style="font-family:monospace;font-size:10px;">
                  {{ e.user }}
                </span>
              </td>
              <td>
                <span class="action-tag" :class="actionTagClass(e.action)">{{ e.action }}</span>
              </td>
              <td class="detail-cell text-muted">{{ e.detail || '—' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else-if="loading" class="audit-empty">Lade …</div>
        <div v-else class="audit-empty text-muted">
          Keine Einträge.
          <span v-if="filterUser || filterAction || filterDetail">Filter anpassen oder</span>
          <span v-else>Noch keine Aktionen aufgezeichnet.</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

interface AuditEntry { ts: string; user: string; action: string; detail: string; }

const auth    = useAuthStore();
const entries = ref<AuditEntry[]>([]);
const loading = ref(false);
const message = ref('');
const msgType = ref<'success' | 'error'>('success');
const limitVal    = ref(500);
const filterUser   = ref('');
const filterAction = ref('');
const filterDetail = ref('');

function flash(msg: string, type: 'success' | 'error' = 'success') {
  message.value = msg; msgType.value = type;
  setTimeout(() => { message.value = ''; }, 4000);
}

const filtered = computed(() => {
  let list = entries.value;
  if (filterUser.value)
    list = list.filter(e => e.user.toLowerCase().includes(filterUser.value.toLowerCase()));
  if (filterAction.value)
    list = list.filter(e => e.action.toLowerCase().includes(filterAction.value.toLowerCase()));
  if (filterDetail.value)
    list = list.filter(e => e.detail.toLowerCase().includes(filterDetail.value.toLowerCase()));
  return list;
});

function applyFilter() { /* reactivity handles it */ }

async function load() {
  loading.value = true;
  try {
    await auth.initialize();
    const res = await apiClient.get('/audit', { params: { limit: limitVal.value } });
    entries.value = res.data.entries ?? [];
  } catch (e: any) {
    flash(e.response?.data?.detail ?? 'Audit-Log konnte nicht geladen werden.', 'error');
  } finally {
    loading.value = false;
  }
}

async function clearLog() {
  if (!confirm('Audit-Log wirklich vollständig leeren? Diese Aktion ist nicht rückgängig zu machen.')) return;
  try {
    await apiClient.delete('/audit');
    entries.value = [];
    flash('Audit-Log geleert.');
  } catch (e: any) {
    flash(e.response?.data?.detail ?? 'Fehler beim Leeren.', 'error');
  }
}

function formatTs(ts: string): string {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString('de-DE', {
      day: '2-digit', month: '2-digit', year: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch { return ts; }
}

function actionTagClass(action: string): string {
  if (action.startsWith('service.stop'))    return 'tag-danger';
  if (action.startsWith('service.'))        return 'tag-warn';
  if (action.startsWith('config.'))         return 'tag-blue';
  if (action.startsWith('user.delete'))     return 'tag-danger';
  if (action.startsWith('user.'))           return 'tag-purple';
  if (action.startsWith('settings.host.delete')) return 'tag-danger';
  if (action.startsWith('settings.'))       return 'tag-gray';
  return 'tag-gray';
}

function actionRowClass(action: string): string {
  if (action.includes('delete') || action === 'service.stop') return 'row-danger';
  if (action.startsWith('service.')) return 'row-warn';
  return '';
}

onMounted(load);
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.text-sm { font-size: 12px; }

.filter-bar { padding: 12px 16px; }
.filter-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
.filter-group { display: flex; flex-direction: column; gap: 3px; min-width: 100px; }
.filter-label { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em; }

.audit-table-wrap { max-height: 70vh; overflow-y: auto; }
.audit-table { font-size: 12px; }
.audit-table th { position: sticky; top: 0; background: var(--bg-muted); z-index: 1; }
.ts-cell { white-space: nowrap; font-family: ui-monospace, monospace; color: var(--text-muted); font-size: 11px; }
.detail-cell { word-break: break-all; font-family: ui-monospace, monospace; font-size: 11px; }
.audit-empty { padding: 24px; text-align: center; font-size: 13px; }

/* Action tags */
.action-tag {
  display: inline-block; padding: 1px 7px; border-radius: 4px;
  font-size: 10px; font-weight: 700; font-family: ui-monospace, monospace; white-space: nowrap;
}
.tag-blue   { background: #dbeafe; color: #1e40af; }
.tag-warn   { background: #fef9c3; color: #854d0e; }
.tag-danger { background: #fee2e2; color: #991b1b; }
.tag-purple { background: #f3e8ff; color: #6b21a8; }
.tag-gray   { background: #f1f5f9; color: #475569; }

/* Row tints */
.row-danger td { background: #fff5f5; }
.row-warn   td { background: #fffbeb; }
</style>

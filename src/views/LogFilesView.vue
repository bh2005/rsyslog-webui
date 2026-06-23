<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Log-Dateien</h1>
        <p>Datei-Explorer für archivierte Logs pro Host</p>
      </div>
      <button class="btn btn-ghost btn-sm" @click="loadTree" :disabled="loading">Aktualisieren</button>
    </div>

    <div v-if="message" :class="['alert', msgType === 'error' ? 'alert-error' : 'alert-success']">{{ message }}</div>

    <div v-if="loading" class="text-muted" style="padding:32px;text-align:center;font-size:13px;">Wird geladen…</div>

    <div v-else-if="!tree.length" class="card">
      <div class="card-body text-muted" style="padding:32px;text-align:center;font-size:13px;">
        Keine Log-Dateien gefunden.<br>
        <span style="font-size:11px;">Erwartet unter <code>/data/syslog/HOSTNAME/YYYY/MM/</code></span>
      </div>
    </div>

    <div v-else class="explorer-layout">

      <!-- ── Tree panel ──────────────────────────────────────────────────── -->
      <div class="tree-panel card">
        <div class="card-header">
          <span>Hosts / Zeitraum</span>
          <span class="text-muted text-sm">{{ totalFiles }} Dateien · {{ formatBytes(totalBytes) }}</span>
        </div>
        <div class="tree-scroll">
          <div v-for="host in tree" :key="host.host" class="tree-host">
            <!-- Host row -->
            <div class="tree-host-header" @click="toggleHost(host.host)"
                 :class="{ 'tree-active': openHosts.has(host.host) }">
              <span class="tree-arrow">{{ openHosts.has(host.host) ? '▾' : '▸' }}</span>
              <svg class="tree-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
              <span class="tree-label">{{ host.host }}</span>
            </div>

            <template v-if="openHosts.has(host.host)">
              <div v-for="year in host.years" :key="year.year" class="tree-year">
                <!-- Year row -->
                <div class="tree-year-header" @click="toggleYear(host.host, year.year)"
                     :class="{ 'tree-active': openYears.has(`${host.host}/${year.year}`) }">
                  <span class="tree-arrow">{{ openYears.has(`${host.host}/${year.year}`) ? '▾' : '▸' }}</span>
                  <svg class="tree-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
                  </svg>
                  <span class="tree-label">{{ year.year }}</span>
                </div>

                <template v-if="openYears.has(`${host.host}/${year.year}`)">
                  <div v-for="month in year.months" :key="month.month" class="tree-month">
                    <!-- Month row -->
                    <div class="tree-month-header" @click="toggleMonth(host.host, year.year, month.month)"
                         :class="{ 'tree-active': openMonths.has(`${host.host}/${year.year}/${month.month}`) }">
                      <span class="tree-arrow">{{ openMonths.has(`${host.host}/${year.year}/${month.month}`) ? '▾' : '▸' }}</span>
                      <svg class="tree-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><path d="M16 3v4M8 3v4M3 11h18"/>
                      </svg>
                      <span class="tree-label">{{ monthName(month.month) }}</span>
                      <span class="tree-count">{{ month.files.length }}</span>
                    </div>

                    <!-- File rows -->
                    <template v-if="openMonths.has(`${host.host}/${year.year}/${month.month}`)">
                      <div v-for="f in month.files" :key="f.path"
                           class="tree-file"
                           :class="{ 'tree-file-selected': selectedFile?.path === f.path }"
                           @click="selectFile(f)">
                        <svg class="tree-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
                        </svg>
                        <span class="tree-label">{{ f.name }}</span>
                        <span class="tree-size">{{ formatBytes(f.size) }}</span>
                      </div>
                    </template>
                  </div>
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ── Detail panel ───────────────────────────────────────────────── -->
      <div class="detail-panel card">
        <div v-if="!selectedFile" class="card-body text-muted" style="padding:48px;text-align:center;font-size:13px;">
          Datei aus dem Explorer auswählen.
        </div>
        <template v-else>
          <div class="card-header">
            <span class="font-mono" style="font-size:13px;">{{ selectedFile.name }}</span>
            <button class="btn btn-primary btn-sm" @click="download(selectedFile.path)">↓ Herunterladen</button>
          </div>
          <div class="card-body">
            <div class="detail-grid">
              <div class="detail-item">
                <span class="meta-label">Pfad</span>
                <span class="meta-value font-mono" style="font-size:11px;word-break:break-all;">{{ selectedFile.path }}</span>
              </div>
              <div class="detail-item">
                <span class="meta-label">Größe</span>
                <span class="meta-value">{{ formatBytes(selectedFile.size) }}</span>
              </div>
              <div class="detail-item">
                <span class="meta-label">Zuletzt geändert</span>
                <span class="meta-value">{{ formatDate(selectedFile.modified) }}</span>
              </div>
            </div>
          </div>
          <div class="preview-hint">
            <div class="preview-hint-text">
              Log-Dateien können direkt heruntergeladen werden.
              Zur Analyse die <router-link to="/logs">Log-Ansicht</router-link> verwenden.
            </div>
            <button class="btn btn-primary" @click="download(selectedFile.path)">
              ↓ {{ selectedFile.name }} herunterladen
            </button>
          </div>
        </template>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { apiClient } from '../api';

interface LogFile   { name: string; path: string; size: number; modified: string; }
interface MonthNode { month: string; files: LogFile[]; }
interface YearNode  { year: string; months: MonthNode[]; }
interface HostNode  { host: string; years: YearNode[]; }

const tree       = ref<HostNode[]>([]);
const totalFiles = ref(0);
const totalBytes = ref(0);
const loading    = ref(false);
const message    = ref('');
const msgType    = ref<'success' | 'error'>('success');

const selectedFile = ref<LogFile | null>(null);
const openHosts  = ref<Set<string>>(new Set());
const openYears  = ref<Set<string>>(new Set());
const openMonths = ref<Set<string>>(new Set());

const MONTHS = ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'];
function monthName(m: string) {
  const n = parseInt(m, 10);
  return isNaN(n) ? m : (MONTHS[n - 1] ?? m);
}

function flash(msg: string, type: 'success' | 'error' = 'success') {
  message.value = msg; msgType.value = type;
  setTimeout(() => { message.value = ''; }, 4000);
}

async function loadTree() {
  loading.value = true;
  try {
    const res = await apiClient.get('/rsyslog/files');
    tree.value       = res.data.tree ?? [];
    totalFiles.value = res.data.total_files ?? 0;
    totalBytes.value = res.data.total_bytes ?? 0;
    // Auto-expand if only one host
    if (tree.value.length === 1) {
      openHosts.value.add(tree.value[0].host);
    }
  } catch (e: any) {
    flash(e.response?.data?.detail ?? 'Fehler beim Laden der Log-Dateien.', 'error');
  } finally {
    loading.value = false;
  }
}

function toggleHost(host: string) {
  openHosts.value.has(host) ? openHosts.value.delete(host) : openHosts.value.add(host);
}
function toggleYear(host: string, year: string) {
  const key = `${host}/${year}`;
  openYears.value.has(key) ? openYears.value.delete(key) : openYears.value.add(key);
}
function toggleMonth(host: string, year: string, month: string) {
  const key = `${host}/${year}/${month}`;
  openMonths.value.has(key) ? openMonths.value.delete(key) : openMonths.value.add(key);
}
function selectFile(f: LogFile) {
  selectedFile.value = f;
}

function download(path: string) {
  window.open(`/api/rsyslog/files/download?path=${encodeURIComponent(path)}`, '_blank');
}

function formatBytes(bytes: number): string {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

function formatDate(iso: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' });
  } catch { return iso; }
}

onMounted(loadTree);
</script>

<style scoped>
.explorer-layout { display: flex; gap: 16px; align-items: flex-start; }

/* Tree panel */
.tree-panel  { width: 300px; flex-shrink: 0; }
.detail-panel { flex: 1; min-width: 0; }
.tree-scroll { max-height: calc(100vh - 200px); overflow-y: auto; }

/* Host / Year / Month / File rows */
.tree-host { }
.tree-host-header, .tree-year-header, .tree-month-header, .tree-file {
  display: flex; align-items: center; gap: 6px; cursor: pointer;
  padding: 5px 10px; font-size: 13px; border-radius: 4px;
  transition: background .1s; user-select: none;
}
.tree-host-header { font-weight: 600; padding: 7px 10px; border-bottom: 1px solid var(--border-soft); }
.tree-year-header { padding-left: 20px; font-weight: 500; }
.tree-month-header{ padding-left: 34px; color: var(--text-muted); }
.tree-file        { padding-left: 48px; color: var(--text-muted); font-size: 12px; font-family: ui-monospace,monospace; }

.tree-host-header:hover,
.tree-year-header:hover,
.tree-month-header:hover,
.tree-file:hover { background: var(--ks-50); }

.tree-active { color: var(--ks-700); }
.tree-file-selected { background: var(--ks-100) !important; color: var(--ks-800) !important; }

.tree-arrow { font-size: 11px; width: 12px; color: var(--text-muted); }
.tree-icon  { width: 14px; height: 14px; flex-shrink: 0; opacity: .6; }
.tree-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-count { font-size: 10px; background: var(--ks-100); color: var(--ks-700); padding: 1px 5px;
  border-radius: 9px; font-weight: 600; flex-shrink: 0; }
.tree-size  { font-size: 10px; color: var(--text-muted); flex-shrink: 0; }

/* Detail panel */
.detail-grid  { display: flex; flex-direction: column; gap: 10px; }
.detail-item  { display: flex; flex-direction: column; gap: 2px; }
.preview-hint { border-top: 1px solid var(--border); padding: 24px; display: flex;
  align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.preview-hint-text { font-size: 13px; color: var(--text-muted); }
.preview-hint-text a { color: var(--ks-500); }
.font-mono { font-family: ui-monospace, monospace; }
.text-sm   { font-size: 12px; }
</style>

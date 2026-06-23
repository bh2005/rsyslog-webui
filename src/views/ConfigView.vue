<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Konfiguration</h1>
        <p>rsyslog.conf und inkludierte Dateien</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-ghost btn-sm"
          @click="activeTab === 'main' ? loadConfig() : activeTab === 'includes' ? loadIncludes() : activeTab === 'receiver' ? loadReceiverHosts() : loadHistory()"
          :disabled="saving">Aktualisieren</button>

        <template v-if="activeTab === 'main'">
          <button class="btn btn-ghost btn-sm" @click="downloadConfig" title="rsyslog.conf herunterladen">↓ Download</button>
          <label class="btn btn-ghost btn-sm" title="Config-Datei hochladen und wiederherstellen" style="cursor:pointer;">
            ↑ Restore
            <input type="file" accept=".conf,.txt" style="display:none" @change="restoreConfig" />
          </label>
          <button class="btn btn-secondary btn-sm" @click="checkSyntax" :disabled="!config?.editable || checking">
            {{ checking ? 'Prüft …' : 'Syntax prüfen' }}
          </button>
          <button class="btn btn-secondary btn-sm" @click="reloadConfig" :disabled="!canReload || saving">
            Dienst neu laden
          </button>
          <button class="btn btn-primary btn-sm" @click="saveConfig" :disabled="!config?.editable || saving">
            Speichern
          </button>
        </template>

        <template v-else-if="activeTab === 'includes' && selectedFile && !selectedFile.managed">
          <button class="btn btn-secondary btn-sm" @click="checkIncludeSyntax" :disabled="!canEdit || checkingInclude">
            {{ checkingInclude ? 'Prüft …' : 'Syntax prüfen' }}
          </button>
          <button class="btn btn-primary btn-sm" @click="saveInclude" :disabled="!canEdit || saving">Speichern</button>
          <button class="btn btn-danger btn-sm" @click="deleteInclude" :disabled="!canDelete || saving">Löschen</button>
        </template>
      </div>
    </div>

    <div v-if="message" :class="['alert', messageType === 'error' ? 'alert-error' : 'alert-success']">{{ message }}</div>

    <!-- Syntax check result -->
    <div v-if="checkResult" :class="['check-result', checkResult.ok ? 'check-ok' : (checkResult.ok === false ? 'check-fail' : 'check-warn')]">
      <div class="check-header">
        <span class="check-icon">
          <svg v-if="checkResult.ok"            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
          <svg v-else-if="checkResult.ok===false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/></svg>
          <svg v-else                            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </span>
        <span class="check-title">{{ checkResult.ok ? 'Syntax OK' : checkResult.ok === false ? 'Syntaxfehler' : 'Prüfung nicht möglich' }}</span>
        <button class="check-close" @click="checkResult = null">✕</button>
      </div>
      <pre v-if="checkResult.output" class="check-output">{{ checkResult.output }}</pre>
    </div>

    <!-- Tabs -->
    <div class="tab-bar mb-4">
      <button class="tab-btn" :class="{ active: activeTab === 'main' }"
        @click="activeTab = 'main'; checkResult = null">rsyslog.conf</button>
      <button class="tab-btn" :class="{ active: activeTab === 'includes' }"
        @click="activeTab = 'includes'; checkResult = null; loadIncludes()">
        /etc/rsyslog.d/
        <span v-if="includeFiles.length" class="tab-count">{{ includeFiles.length }}</span>
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'receiver' }"
        @click="activeTab = 'receiver'; checkResult = null; loadReceiverHosts()">
        Lookup-Tabellen
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'history' }"
        @click="activeTab = 'history'; checkResult = null; loadHistory()">
        Historie
        <span v-if="snapshots.length" class="tab-count">{{ snapshots.length }}</span>
      </button>
    </div>

    <!-- ── Tab: rsyslog.conf ─────────────────────────────────────────────── -->
    <template v-if="activeTab === 'main'">
      <div class="card mb-4">
        <div class="card-header">Dateiinfo</div>
        <div class="card-body">
          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">Pfad</span>
              <span class="meta-value font-mono" style="font-size:12px;">{{ config?.config_path ?? '—' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Letzte Änderung</span>
              <span class="meta-value">{{ config?.last_modified ?? '—' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Berechtigung</span>
              <span class="badge" :class="config?.editable ? 'badge-green' : 'badge-gray'">
                {{ config?.editable ? 'Editierbar' : 'Nur Lesen' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header">
          <span>Inhalt</span>
          <span class="text-muted text-sm">{{ lineCount }} Zeilen</span>
        </div>
        <div class="card-body" style="padding:0;">
          <textarea v-model="content" class="code-editor" :readonly="!config?.editable" spellcheck="false" />
        </div>
      </div>
    </template>

    <!-- ── Tab: /etc/rsyslog.d/ ─────────────────────────────────────────── -->
    <template v-else-if="activeTab === 'includes'">
      <div class="include-layout">
        <div class="include-list card">
          <div class="card-header"><span>Dateien</span></div>
          <div v-if="includeFiles.length === 0" class="card-body text-muted" style="font-size:13px;">Keine .conf-Dateien.</div>
          <ul v-else class="file-list">
            <li v-for="f in includeFiles" :key="f.name" class="file-item"
                :class="{ 'file-active': selectedFile?.name === f.name }" @click="openInclude(f)">
              <div class="file-name font-mono">{{ f.name }}</div>
              <div class="file-meta">
                <span v-if="f.managed" class="badge badge-gray" style="font-size:9px;">managed</span>
                <span v-else-if="f.type === 'json'" class="badge badge-blue" style="font-size:9px;">lookup</span>
                <span class="text-muted" style="font-size:10px;">{{ formatSize(f.size) }}</span>
              </div>
            </li>
          </ul>
        </div>
        <div class="include-editor card">
          <div v-if="!selectedFile" class="card-body text-muted" style="padding:32px;text-align:center;font-size:13px;">
            Datei auswählen.
          </div>
          <template v-else>
            <div class="card-header">
              <span class="font-mono" style="font-size:13px;">{{ selectedFile.name }}</span>
              <div style="display:flex;gap:8px;align-items:center;">
                <span v-if="selectedFile.managed" class="badge badge-gray">managed</span>
                <span class="text-muted text-sm">{{ includeLineCount }} Zeilen · {{ formatSize(selectedFile.size) }}</span>
              </div>
            </div>
            <div v-if="selectedFile.managed" class="card-body" style="padding:10px 16px;">
              <div class="alert alert-info" style="margin:0;font-size:12px;">
                Managed-Datei — Änderungen über die Einstellungen vornehmen.
              </div>
            </div>
            <div class="card-body" style="padding:0;">
              <textarea v-model="includeContent" class="code-editor"
                        :readonly="selectedFile.managed || !canEdit" spellcheck="false" />
            </div>
          </template>
        </div>
      </div>
    </template>

    <!-- ── Tab: Historie ─────────────────────────────────────────────────── -->
    <template v-else>
      <div class="history-layout">
        <!-- Snapshot list -->
        <div class="include-list card">
          <div class="card-header"><span>Snapshots</span></div>
          <div v-if="snapshots.length === 0" class="card-body text-muted" style="font-size:13px;">
            Noch keine Snapshots. Werden beim nächsten Speichern angelegt.
          </div>
          <ul v-else class="file-list">
            <li v-for="s in snapshots" :key="s.name" class="file-item"
                :class="{ 'file-active': selectedSnap?.name === s.name }" @click="openSnapshot(s)">
              <div class="file-name" style="font-size:12px;">{{ s.label }}</div>
              <div class="file-meta">
                <span class="text-muted" style="font-size:10px;">{{ formatSize(s.size) }}</span>
              </div>
            </li>
          </ul>
        </div>

        <!-- Diff / restore -->
        <div class="include-editor card">
          <div v-if="!selectedSnap" class="card-body text-muted" style="padding:32px;text-align:center;font-size:13px;">
            Snapshot aus der Liste auswählen.
          </div>
          <template v-else>
            <div class="card-header">
              <span>{{ selectedSnap.label }}</span>
              <div style="display:flex;gap:8px;">
                <button class="btn btn-ghost btn-sm" @click="showDiff = !showDiff">
                  {{ showDiff ? 'Quelltext' : 'Diff anzeigen' }}
                  <span v-if="snapDiffLines > 0" class="tab-count">{{ snapDiffLines }}</span>
                </button>
                <button v-if="canDelete" class="btn btn-secondary btn-sm"
                        @click="rollback(selectedSnap.name)" :disabled="saving">
                  Wiederherstellen
                </button>
              </div>
            </div>

            <!-- Diff view -->
            <template v-if="showDiff">
              <div v-if="!snapDiff" class="card-body text-muted" style="font-size:13px;">Kein Diff verfügbar (Dateien identisch).</div>
              <div v-else class="diff-view">
                <div v-for="(line, i) in diffLines" :key="i"
                     :class="['diff-line', line.startsWith('+') && !line.startsWith('+++') ? 'diff-add' : line.startsWith('-') && !line.startsWith('---') ? 'diff-del' : line.startsWith('@@') ? 'diff-hunk' : '']">
                  <span class="diff-text">{{ line }}</span>
                </div>
              </div>
            </template>
            <!-- Source view -->
            <template v-else>
              <div class="card-body" style="padding:0;">
                <textarea :value="snapContent" class="code-editor" readonly spellcheck="false" />
              </div>
            </template>
          </template>
        </div>
      </div>
    </template>

    <!-- ── Tab: Lookup-Tabellen ─────────────────────────────────────────────── -->
    <template v-if="activeTab === 'receiver'">

      <!-- Create new table -->
      <div v-if="canEdit" class="card mb-4">
        <div class="card-header">Neue Lookup-Tabelle anlegen</div>
        <div class="card-body">
          <div style="display:flex;gap:8px;align-items:center;">
            <span style="font-size:12px;color:var(--text-muted);white-space:nowrap;">lookup_</span>
            <input v-model="newTableName" class="input input-sm" placeholder="mein_geraet"
                   style="width:180px;" @keyup.enter="createLookupTable" />
            <span style="font-size:12px;color:var(--text-muted);">.json</span>
            <button class="btn btn-primary btn-sm" @click="createLookupTable"
                    :disabled="!newTableName.trim() || creatingTable">
              {{ creatingTable ? 'Erstelle…' : 'Erstellen' }}
            </button>
          </div>
        </div>
      </div>

      <!-- No tables -->
      <div v-if="lookupTables.length === 0" class="card">
        <div class="card-body text-muted" style="text-align:center;padding:24px;font-size:13px;">
          Keine Lookup-Tabellen (lookup_*.json) in /etc/rsyslog.d/ gefunden.
        </div>
      </div>

      <!-- One card per table -->
      <div v-for="t in lookupTables" :key="t.filename" class="card mb-4">
        <div class="card-header">
          <span class="font-mono" style="font-size:13px;">{{ t.filename }}</span>
          <div style="display:flex;gap:8px;align-items:center;">
            <span class="badge badge-blue" style="font-size:10px;">{{ t.name }}</span>
            <span v-if="t.dirty" class="badge badge-yellow" style="font-size:10px;">ungespeichert</span>
          </div>
        </div>
        <div class="card-body" style="padding:0;">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width:200px;">IP-Adresse</th>
                <th>Hostname / Wert</th>
                <th style="width:80px;" v-if="canEdit"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, i) in t.entries" :key="i">
                <td>
                  <input v-if="canEdit" v-model="entry.index" class="input input-sm font-mono"
                         placeholder="10.0.0.1" style="width:100%;" @input="markDirty(t)" />
                  <span v-else class="font-mono">{{ entry.index }}</span>
                </td>
                <td>
                  <input v-if="canEdit" v-model="entry.value" class="input input-sm"
                         placeholder="server01" style="width:100%;" @input="markDirty(t)" />
                  <span v-else>{{ entry.value }}</span>
                </td>
                <td v-if="canEdit">
                  <button class="btn btn-danger btn-sm" @click="removeEntry(t, i)">×</button>
                </td>
              </tr>
              <tr v-if="t.entries.length === 0">
                <td colspan="3" class="text-muted" style="text-align:center;padding:10px;font-size:12px;">
                  Keine Einträge.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="canEdit" class="card-body" style="border-top:1px solid var(--border-soft);display:flex;gap:8px;justify-content:space-between;">
          <button class="btn btn-ghost btn-sm" @click="addEntry(t)">+ Eintrag</button>
          <button class="btn btn-primary btn-sm" @click="saveLookupTable(t)"
                  :disabled="!t.dirty || saving">
            {{ saving ? 'Wird gespeichert…' : 'Speichern + rsyslog reload' }}
          </button>
        </div>
      </div>

    </template>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

interface CheckResult  { ok: boolean | null; output: string; returncode: number; }
interface IncludeFile  { name: string; size: number; modified: string; managed: boolean; type?: string; }
interface Snapshot     { name: string; label: string; size: number; }

const auth = useAuthStore();
const canReload = computed(() => auth.isAdmin || auth.isOperator);
const canEdit   = computed(() => auth.isAdmin || auth.isOperator);
const canDelete = computed(() => auth.isAdmin);

const activeTab  = ref<'main' | 'includes' | 'history' | 'receiver'>('main');
const message    = ref('');
const messageType = ref<'success' | 'error'>('success');
const saving     = ref(false);
const checkResult = ref<CheckResult | null>(null);

// Main config
const config  = ref<Record<string, string | boolean> | null>(null);
const content = ref('');
const checking = ref(false);
const lineCount = computed(() => content.value ? content.value.split('\n').length : 0);

// Includes
const includeFiles    = ref<IncludeFile[]>([]);
const selectedFile    = ref<IncludeFile | null>(null);
const includeContent  = ref('');
const checkingInclude = ref(false);
const includeLineCount = computed(() => includeContent.value ? includeContent.value.split('\n').length : 0);

// History
const snapshots     = ref<Snapshot[]>([]);
const selectedSnap  = ref<Snapshot | null>(null);
const snapContent   = ref('');
const snapDiff      = ref('');
const snapDiffLines = ref(0);
const showDiff      = ref(false);
const diffLines     = computed(() => snapDiff.value.split('\n'));

function flash(msg: string, type: 'success' | 'error' = 'success') {
  message.value = msg; messageType.value = type;
  setTimeout(() => { message.value = ''; }, 4000);
}

// ── Main config ──────────────────────────────────────────────────────────────

async function loadConfig() {
  try {
    await auth.initialize();
    const res = await apiClient.get('/rsyslog/config');
    config.value  = res.data;
    content.value = res.data.content;
    checkResult.value = null;
  } catch { flash('Konfiguration konnte nicht geladen werden.', 'error'); }
}

async function checkSyntax() {
  checking.value = true; checkResult.value = null;
  try {
    const res = await apiClient.post('/rsyslog/config/check', { content: content.value });
    checkResult.value = res.data;
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { checking.value = false; }
}

async function saveConfig() {
  if (!config.value?.editable) return;
  saving.value = true;
  try {
    await apiClient.put('/rsyslog/config', { content: content.value });
    flash('Konfiguration gespeichert.');
    await Promise.all([loadConfig(), loadHistory()]);
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { saving.value = false; }
}

async function reloadConfig() {
  saving.value = true;
  try {
    await apiClient.post('/rsyslog/reload');
    flash('Dienst erfolgreich neu geladen.');
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { saving.value = false; }
}

function downloadConfig() {
  window.open('/api/rsyslog/config/download', '_blank');
}

async function restoreConfig(evt: Event) {
  const input = evt.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  saving.value = true;
  try {
    await apiClient.post('/rsyslog/config/restore', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    flash(`"${file.name}" wiederhergestellt.`);
    await Promise.all([loadConfig(), loadHistory()]);
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Restore fehlgeschlagen.', 'error'); }
  finally { saving.value = false; input.value = ''; }
}

// ── Includes ─────────────────────────────────────────────────────────────────

async function loadIncludes() {
  try {
    const res = await apiClient.get('/rsyslog/includes');
    includeFiles.value = res.data.files ?? [];
    if (selectedFile.value) {
      const up = includeFiles.value.find(f => f.name === selectedFile.value!.name);
      if (up) selectedFile.value = up;
    }
  } catch { flash('Include-Dateien konnten nicht geladen werden.', 'error'); }
}

async function openInclude(f: IncludeFile) {
  selectedFile.value = f; checkResult.value = null;
  try {
    const res = await apiClient.get(`/rsyslog/includes/${f.name}`);
    includeContent.value = res.data.content;
    selectedFile.value = { ...f, managed: res.data.managed };
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
}

async function checkIncludeSyntax() {
  checkingInclude.value = true; checkResult.value = null;
  try {
    const res = await apiClient.post('/rsyslog/config/check', { content: includeContent.value });
    checkResult.value = res.data;
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { checkingInclude.value = false; }
}

async function saveInclude() {
  if (!selectedFile.value || selectedFile.value.managed) return;
  saving.value = true;
  try {
    await apiClient.put(`/rsyslog/includes/${selectedFile.value.name}`, { content: includeContent.value });
    flash(`${selectedFile.value.name} gespeichert.`);
    await loadIncludes();
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { saving.value = false; }
}

async function deleteInclude() {
  if (!selectedFile.value || !confirm(`"${selectedFile.value.name}" wirklich löschen?`)) return;
  saving.value = true;
  try {
    await apiClient.delete(`/rsyslog/includes/${selectedFile.value.name}`);
    flash(`${selectedFile.value.name} gelöscht.`);
    selectedFile.value = null; includeContent.value = '';
    await loadIncludes();
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { saving.value = false; }
}

// ── History ──────────────────────────────────────────────────────────────────

async function loadHistory() {
  try {
    const res = await apiClient.get('/rsyslog/config/history');
    snapshots.value = res.data.snapshots ?? [];
  } catch { /* non-critical */ }
}

async function openSnapshot(s: Snapshot) {
  selectedSnap.value = s; showDiff.value = false;
  try {
    const res = await apiClient.get(`/rsyslog/config/history/${s.name}`);
    snapContent.value   = res.data.content;
    snapDiff.value      = res.data.diff ?? '';
    snapDiffLines.value = res.data.diff_lines ?? 0;
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
}

async function rollback(snapshotName: string) {
  if (!confirm(`Konfiguration auf Snapshot "${selectedSnap.value?.label}" zurücksetzen?`)) return;
  saving.value = true;
  try {
    await apiClient.post('/rsyslog/config/rollback', { snapshot: snapshotName });
    flash('Konfiguration wiederhergestellt. Dienst bitte neu laden.');
    await Promise.all([loadConfig(), loadHistory()]);
    activeTab.value = 'main';
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { saving.value = false; }
}

// ── Lookup Tables ─────────────────────────────────────────────────────────────

interface LookupEntry { index: string; value: string; }
interface LookupTable { filename: string; name: string; entries: LookupEntry[]; dirty?: boolean; }

const lookupTables  = ref<LookupTable[]>([]);
const newTableName  = ref('');
const creatingTable = ref(false);

async function loadReceiverHosts() {
  try {
    const res = await apiClient.get('/rsyslog/lookup-tables');
    // Deep clone so edits don't mutate originals until save
    lookupTables.value = (res.data.tables ?? []).map((t: LookupTable) => ({
      ...t,
      entries: t.entries.map(e => ({ ...e })),
      dirty: false,
    }));
  } catch { flash('Lookup-Tabellen konnten nicht geladen werden.', 'error'); }
}

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
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
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
    flash(`${filename} erstellt.`);
    await loadReceiverHosts();
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { creatingTable.value = false; }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

onMounted(async () => {
  await loadConfig();
  loadHistory();
});
</script>

<style scoped>
.mb-4  { margin-bottom: 16px; }
.text-sm { font-size: 12px; }
.font-mono { font-family: ui-monospace, monospace; }

/* Tabs */
.tab-bar { display: flex; gap: 4px; border-bottom: 2px solid var(--border); padding-bottom: 0; }
.tab-btn { padding: 7px 16px; font-size: 13px; font-weight: 500; border: none; background: none;
  cursor: pointer; color: var(--text-muted); border-bottom: 2px solid transparent;
  margin-bottom: -2px; border-radius: 4px 4px 0 0; display: flex; align-items: center; gap: 6px; }
.tab-btn:hover { color: var(--ks-600); background: var(--ks-50); }
.tab-btn.active { color: var(--ks-700); border-bottom-color: var(--ks-500); font-weight: 600; }
.tab-count { background: var(--ks-100); color: var(--ks-700); font-size: 10px; font-weight: 700;
  padding: 1px 5px; border-radius: 9px; }

/* Include / History layout */
.include-layout, .history-layout { display: flex; gap: 16px; align-items: flex-start; }
.include-list { width: 220px; flex-shrink: 0; }
.include-editor { flex: 1; min-width: 0; }
.file-list { list-style: none; margin: 0; padding: 0; }
.file-item { padding: 8px 14px; cursor: pointer; border-bottom: 1px solid var(--border-soft); transition: background .1s; }
.file-item:hover { background: var(--ks-50); }
.file-active { background: var(--ks-100) !important; }
.file-name { font-size: 12px; font-family: ui-monospace, monospace; word-break: break-all; }
.file-meta { display: flex; gap: 6px; align-items: center; margin-top: 2px; }

/* Diff view */
.diff-view { font-family: ui-monospace, monospace; font-size: 11.5px; overflow-x: auto;
  max-height: 65vh; overflow-y: auto; padding: 0; }
.diff-line { padding: 0 12px; line-height: 1.6; white-space: pre; }
.diff-add  { background: #dcfce7; color: #14532d; }
.diff-del  { background: #fee2e2; color: #7f1d1d; }
.diff-hunk { background: #eff6ff; color: #1e40af; font-weight: 600; }
.diff-text { display: block; }

/* Check result */
.check-result { border-radius: 8px; border: 1.5px solid; margin-bottom: 16px; overflow: hidden; }
.check-ok   { border-color: #86efac; background: #f0fdf4; }
.check-fail { border-color: #fca5a5; background: #fef2f2; }
.check-warn { border-color: #fcd34d; background: #fffbeb; }
.check-header { display: flex; align-items: center; gap: 8px; padding: 10px 14px; font-weight: 600; font-size: 13px; }
.check-ok .check-header { color: #166534; }
.check-fail .check-header { color: #991b1b; }
.check-warn .check-header { color: #92400e; }
.check-icon svg { width: 18px; height: 18px; }
.check-title { flex: 1; }
.check-close { background: none; border: none; cursor: pointer; font-size: 14px; padding: 0 4px; opacity: .6; }
.check-close:hover { opacity: 1; }
.check-output { margin: 0; padding: 10px 14px; border-top: 1px solid rgba(0,0,0,.08);
  font-family: ui-monospace, monospace; font-size: 11.5px; white-space: pre-wrap;
  max-height: 200px; overflow-y: auto; }
.check-ok   .check-output { background: #dcfce7; color: #14532d; }
.check-fail .check-output { background: #fee2e2; color: #7f1d1d; }
.check-warn .check-output { background: #fef9c3; color: #78350f; }
</style>

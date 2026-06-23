<template>
  <div class="manuals-layout">
    <!-- Left: file list -->
    <aside class="manuals-sidebar">
      <div class="manuals-sidebar-header">
        <span class="manuals-sidebar-title">Handbücher &amp; Dokumentation</span>
        <label v-if="isAdmin" class="btn btn-sm btn-primary upload-btn" title="HTML-Datei hochladen">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14" style="flex-shrink:0">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
          </svg>
          Hochladen
          <input type="file" accept=".html,.htm" style="display:none" @change="handleUpload" />
        </label>
      </div>

      <div v-if="loading" class="manuals-loading">Lade…</div>
      <div v-else-if="error" class="manuals-error">{{ error }}</div>
      <div v-else>
        <template v-for="cat in categories" :key="cat">
          <div class="manuals-category">{{ cat }}</div>
          <div
            v-for="f in byCategory(cat)"
            :key="f.name"
            class="manuals-item"
            :class="{ active: selected?.name === f.name }"
            @click="select(f)"
          >
            <svg class="manuals-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <div class="manuals-item-info">
              <div class="manuals-item-name">{{ f.name }}</div>
              <div class="manuals-item-meta">{{ formatSize(f.size) }}<span v-if="f.readonly" class="manuals-ro"> · Schreibgeschützt</span></div>
            </div>
            <button
              v-if="isAdmin && !f.readonly"
              class="manuals-delete"
              title="Löschen"
              @click.stop="confirmDelete(f)"
            >✕</button>
          </div>
        </template>
        <div v-if="files.length === 0" class="manuals-empty">Keine Dateien vorhanden.</div>
      </div>
    </aside>

    <!-- Right: iframe viewer -->
    <main class="manuals-main">
      <div v-if="!selected" class="manuals-placeholder">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="manuals-placeholder-icon">
          <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
        </svg>
        <p>Datei aus der Liste auswählen, um sie anzuzeigen.</p>
      </div>
      <iframe
        v-else
        :src="iframeSrc"
        class="manuals-iframe"
        :title="selected.name"
        sandbox="allow-same-origin allow-scripts allow-popups"
      />
    </main>

    <!-- Delete confirm modal -->
    <div v-if="deleteTarget" class="pw-overlay" @click.self="deleteTarget = null">
      <div class="pw-modal">
        <div class="pw-header">
          <span>Datei löschen</span>
          <button class="pw-close" @click="deleteTarget = null">✕</button>
        </div>
        <div class="pw-body">
          <p style="font-size:14px;">Soll <strong>{{ deleteTarget.name }}</strong> wirklich gelöscht werden?</p>
        </div>
        <div class="pw-footer">
          <button class="btn btn-ghost" @click="deleteTarget = null">Abbrechen</button>
          <button class="btn btn-danger" @click="doDelete" :disabled="deleting">
            {{ deleting ? 'Wird gelöscht…' : 'Löschen' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { apiClient } from '../api';
import { useAuthStore } from '../stores/auth';

interface ManualFile {
  name: string;
  category: string;
  size: number;
  readonly: boolean;
}

const auth     = useAuthStore();
const isAdmin  = computed(() => auth.isAdmin);

const files    = ref<ManualFile[]>([]);
const loading  = ref(true);
const error    = ref('');
const selected = ref<ManualFile | null>(null);
const iframeSrc = computed(() => selected.value ? `/api/manuals/${encodeURIComponent(selected.value.name)}/content` : '');

const categories = computed(() => {
  const seen = new Set<string>();
  files.value.forEach(f => seen.add(f.category));
  return Array.from(seen);
});

function byCategory(cat: string) {
  return files.value.filter(f => f.category === cat);
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

async function load() {
  loading.value = true; error.value = '';
  try {
    const r = await apiClient.get('/manuals');
    files.value = r.data.files ?? [];
    if (files.value.length > 0 && !selected.value) select(files.value[0]);
  } catch {
    error.value = 'Fehler beim Laden der Dateien.';
  } finally {
    loading.value = false;
  }
}

function select(f: ManualFile) {
  selected.value = f;
}

// ── Upload ──────────────────────────────────────────────────────────────────
async function handleUpload(e: Event) {
  const input = e.target as HTMLInputElement;
  const file  = input.files?.[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    await apiClient.post('/manuals', form, { headers: { 'Content-Type': 'multipart/form-data' } });
    await load();
  } catch (err: any) {
    alert(err.response?.data?.detail ?? 'Upload fehlgeschlagen.');
  }
  input.value = '';
}

// ── Delete ──────────────────────────────────────────────────────────────────
const deleteTarget = ref<ManualFile | null>(null);
const deleting     = ref(false);

function confirmDelete(f: ManualFile) {
  deleteTarget.value = f;
}

async function doDelete() {
  if (!deleteTarget.value) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/manuals/${encodeURIComponent(deleteTarget.value.name)}`);
    if (selected.value?.name === deleteTarget.value.name) selected.value = null;
    await load();
  } catch (err: any) {
    alert(err.response?.data?.detail ?? 'Löschen fehlgeschlagen.');
  } finally {
    deleting.value = false;
    deleteTarget.value = null;
  }
}

onMounted(load);
</script>

<style scoped>
.manuals-layout {
  display: flex;
  height: calc(100vh - 0px);
  overflow: hidden;
}

.manuals-sidebar {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f8fafc;
}

.manuals-sidebar-header {
  padding: 14px 16px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 8px;
}

.manuals-sidebar-title {
  font-weight: 600;
  font-size: 13px;
  color: #1e293b;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
  padding: 4px 10px;
  white-space: nowrap;
}

.manuals-category {
  padding: 10px 16px 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: #94a3b8;
}

.manuals-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background .12s;
}

.manuals-item:hover { background: #f1f5f9; }
.manuals-item.active { background: #eff6ff; border-left-color: #3b82f6; }

.manuals-icon {
  width: 16px; height: 16px;
  flex-shrink: 0;
  color: #64748b;
}

.manuals-item.active .manuals-icon { color: #3b82f6; }

.manuals-item-info { flex: 1; min-width: 0; }
.manuals-item-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.manuals-item-meta { font-size: 11px; color: #94a3b8; margin-top: 1px; }
.manuals-ro { color: #f59e0b; }

.manuals-delete {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: #94a3b8;
  padding: 2px 4px;
  border-radius: 3px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity .15s;
}
.manuals-item:hover .manuals-delete { opacity: 1; }
.manuals-delete:hover { background: #fee2e2; color: #ef4444; }

.manuals-loading, .manuals-error, .manuals-empty {
  padding: 20px 16px;
  font-size: 13px;
  color: #94a3b8;
  text-align: center;
}
.manuals-error { color: #ef4444; }

.manuals-main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.manuals-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  gap: 12px;
}
.manuals-placeholder-icon {
  width: 56px; height: 56px;
}
.manuals-placeholder p { font-size: 14px; }

.manuals-iframe {
  flex: 1;
  width: 100%;
  border: none;
}

/* Delete modal reuse */
.pw-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center; z-index: 200; }
.pw-modal { background: white; border-radius: 10px; width: 380px; max-width: 95vw;
  box-shadow: 0 20px 60px rgba(0,0,0,.25); }
.pw-header { display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #e2e8f0; font-weight: 600; font-size: 15px; }
.pw-close { background: none; border: none; cursor: pointer; font-size: 18px; opacity: .5; }
.pw-close:hover { opacity: 1; }
.pw-body { padding: 16px 20px; }
.pw-footer { display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px; border-top: 1px solid #e2e8f0; }

.btn-danger {
  background: #ef4444; color: white; border: none; border-radius: 6px;
  padding: 8px 16px; font-size: 13px; cursor: pointer; font-weight: 500;
}
.btn-danger:hover:not(:disabled) { background: #dc2626; }
.btn-danger:disabled { opacity: .5; cursor: not-allowed; }
</style>

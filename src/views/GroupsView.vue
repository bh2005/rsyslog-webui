<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Gruppen</h1>
        <p>Benutzergruppen für vereinfachte Host-Zuweisung und Alert-Verteilung</p>
      </div>
      <button class="btn btn-primary btn-sm" @click="openCreate">+ Neue Gruppe</button>
    </div>

    <div v-if="message" :class="['alert', msgType === 'error' ? 'alert-error' : 'alert-success']">{{ message }}</div>

    <!-- Group list -->
    <div v-if="!groups.length" class="card">
      <div class="card-body text-muted" style="padding:32px;text-align:center;font-size:13px;">
        Noch keine Gruppen. Gruppen erlauben mehrere Benutzer gemeinsam Hosts zuzuweisen.
      </div>
    </div>

    <div v-else class="groups-grid">
      <div v-for="g in groups" :key="g.name" class="group-card card">
        <div class="group-header">
          <div>
            <div class="group-name">{{ g.display_name || g.name }}</div>
            <div class="group-id font-mono">{{ g.name }}</div>
          </div>
          <div class="group-actions">
            <button class="btn btn-ghost btn-sm" @click="openEdit(g)">Bearbeiten</button>
            <button class="btn btn-danger btn-sm" @click="deleteGroup(g.name)">Löschen</button>
          </div>
        </div>
        <div class="group-body">
          <div class="group-section">
            <div class="group-section-label">Mitglieder ({{ g.members.length }})</div>
            <div class="tag-row">
              <span v-if="!g.members.length" class="text-muted" style="font-size:12px;">Keine</span>
              <span v-for="m in g.members" :key="m" class="badge badge-blue">{{ m }}</span>
            </div>
          </div>
          <div class="group-section">
            <div class="group-section-label">Hosts ({{ g.hosts.length }})</div>
            <div class="tag-row">
              <span v-if="!g.hosts.length" class="text-muted" style="font-size:12px;">Alle (kein Filter)</span>
              <span v-for="h in g.hosts" :key="h" class="badge badge-green">{{ h }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editMode ? 'Gruppe bearbeiten' : 'Neue Gruppe erstellen' }}</h3>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-row" v-if="!editMode">
            <label class="form-label">Gruppen-ID <span class="text-muted">(unveränderlich)</span></label>
            <input v-model="form.name" class="form-input font-mono" placeholder="z.B. linux-team"
                   pattern="[a-z0-9_\-]+" :disabled="editMode" />
          </div>
          <div class="form-row">
            <label class="form-label">Anzeigename</label>
            <input v-model="form.display_name" class="form-input" placeholder="z.B. Linux Team" />
          </div>

          <div class="form-row">
            <label class="form-label">Mitglieder</label>
            <div class="checkbox-grid">
              <label v-if="!availableUsers.length" class="text-muted" style="font-size:12px;">
                Keine Benutzer vorhanden.
              </label>
              <label v-for="u in availableUsers" :key="u.username" class="checkbox-item">
                <input type="checkbox" :value="u.username" v-model="form.members" />
                <span class="checkbox-label">
                  {{ u.username }}
                  <span class="text-muted" style="font-size:10px;">{{ u.role }}</span>
                </span>
              </label>
            </div>
          </div>

          <div class="form-row">
            <label class="form-label">
              Hosts
              <span class="text-muted" style="font-size:11px;">(leer = Gruppe schränkt nicht ein)</span>
            </label>
            <div class="checkbox-grid">
              <label v-if="!availableHosts.length" class="text-muted" style="font-size:12px;">
                Keine Hosts definiert.
              </label>
              <label v-for="h in availableHosts" :key="h.name" class="checkbox-item">
                <input type="checkbox" :value="h.name" v-model="form.hosts" />
                <span class="checkbox-label">
                  {{ h.name }}
                  <span v-if="h.display_name" class="text-muted" style="font-size:10px;">{{ h.display_name }}</span>
                </span>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Abbrechen</button>
          <button class="btn btn-primary" @click="saveGroup" :disabled="saving">
            {{ saving ? 'Wird gespeichert…' : (editMode ? 'Speichern' : 'Erstellen') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { apiClient } from '../api';

interface Group   { name: string; display_name: string; members: string[]; hosts: string[]; }
interface UserRef { username: string; role: string; }
interface HostRef { name: string; display_name: string; ip: string; }

const groups         = ref<Group[]>([]);
const availableUsers = ref<UserRef[]>([]);
const availableHosts = ref<HostRef[]>([]);
const message  = ref('');
const msgType  = ref<'success' | 'error'>('success');
const saving   = ref(false);
const showModal = ref(false);
const editMode  = ref(false);
const form = ref<{ name: string; display_name: string; members: string[]; hosts: string[] }>({
  name: '', display_name: '', members: [], hosts: [],
});

function flash(msg: string, type: 'success' | 'error' = 'success') {
  message.value = msg; msgType.value = type;
  setTimeout(() => { message.value = ''; }, 4000);
}

async function load() {
  const [g, u, h] = await Promise.all([
    apiClient.get('/groups'),
    apiClient.get('/users'),
    apiClient.get('/settings/hosts'),
  ]);
  groups.value         = g.data;
  availableUsers.value = u.data;
  availableHosts.value = h.data;
}

function openCreate() {
  editMode.value = false;
  form.value = { name: '', display_name: '', members: [], hosts: [] };
  showModal.value = true;
}

function openEdit(g: Group) {
  editMode.value = true;
  form.value = { name: g.name, display_name: g.display_name, members: [...g.members], hosts: [...g.hosts] };
  showModal.value = true;
}

function closeModal() { showModal.value = false; }

async function saveGroup() {
  if (!form.value.name.trim()) return;
  saving.value = true;
  try {
    if (editMode.value) {
      await apiClient.put(`/groups/${form.value.name}`, {
        display_name: form.value.display_name,
        members: form.value.members,
        hosts: form.value.hosts,
      });
      flash(`Gruppe "${form.value.name}" gespeichert.`);
    } else {
      await apiClient.post('/groups', form.value);
      flash(`Gruppe "${form.value.name}" erstellt.`);
    }
    closeModal();
    await load();
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { saving.value = false; }
}

async function deleteGroup(name: string) {
  if (!confirm(`Gruppe "${name}" wirklich löschen?`)) return;
  try {
    await apiClient.delete(`/groups/${name}`);
    flash(`Gruppe "${name}" gelöscht.`);
    await load();
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
}

onMounted(load);
</script>

<style scoped>
.groups-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }

.group-card { padding: 0; }
.group-header { display: flex; justify-content: space-between; align-items: flex-start;
  padding: 14px 16px; border-bottom: 1px solid var(--border-soft); }
.group-name { font-weight: 600; font-size: 15px; }
.group-id   { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.group-actions { display: flex; gap: 6px; flex-shrink: 0; }
.group-body { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }
.group-section { }
.group-section-label { font-size: 11px; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
.tag-row { display: flex; flex-wrap: wrap; gap: 4px; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--card-bg); border-radius: 10px; width: 520px; max-width: 95vw;
  max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,.25); }
.modal-header { display: flex; justify-content: space-between; align-items: center;
  padding: 18px 20px; border-bottom: 1px solid var(--border); }
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-close { background: none; border: none; cursor: pointer; font-size: 18px; opacity: .5; }
.modal-close:hover { opacity: 1; }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px;
  padding: 14px 20px; border-top: 1px solid var(--border); }

.form-row { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 13px; font-weight: 500; }

.checkbox-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 6px; max-height: 180px; overflow-y: auto;
  border: 1px solid var(--border); border-radius: 6px; padding: 8px; }
.checkbox-item { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 3px 4px;
  border-radius: 4px; font-size: 13px; }
.checkbox-item:hover { background: var(--ks-50); }
.checkbox-label { display: flex; flex-direction: column; }

.font-mono { font-family: ui-monospace, monospace; }
.text-muted { color: var(--text-muted); }
.text-sm { font-size: 12px; }
</style>

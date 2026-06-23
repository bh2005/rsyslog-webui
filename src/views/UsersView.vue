<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Benutzerverwaltung</h1>
        <p>Benutzer anlegen, Rollen vergeben, E-Mail und Host-Zuweisungen konfigurieren</p>
      </div>
    </div>

    <div v-if="error"      class="alert alert-error">{{ error }}</div>
    <div v-if="successMsg" class="alert alert-success">{{ successMsg }}</div>

    <div class="card mb-5">
      <div class="card-header">Benutzer ({{ users.length }})</div>

      <table class="data-table">
        <thead>
          <tr>
            <th>Benutzername</th>
            <th>Rolle</th>
            <th>E-Mail</th>
            <th>Hosts</th>
            <th style="width:220px;">Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="u in users" :key="u.username">
            <!-- Main row -->
            <tr :class="{ 'row-editing': editingUser?.username === u.username }">
              <td style="font-weight:500;">{{ u.username }}</td>

              <td>
                <template v-if="editingUser?.username === u.username">
                  <select class="select-inline" v-model="editingUser.role">
                    <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
                  </select>
                </template>
                <template v-else>
                  <span class="badge" :class="roleBadge(u.role)">{{ u.role }}</span>
                </template>
              </td>

              <td>
                <template v-if="editingUser?.username === u.username">
                  <input
                    type="email"
                    v-model="editingUser.email"
                    class="input input-sm"
                    placeholder="name@example.com"
                    style="width:180px;"
                  />
                </template>
                <template v-else>
                  <span class="text-muted" style="font-size:12px;">{{ u.email || '—' }}</span>
                </template>
              </td>

              <td>
                <template v-if="editingUser?.username === u.username">
                  <!-- Admins always see everything — no host restriction possible -->
                  <span v-if="editingUser.role === 'admin'" class="text-muted" style="font-size:11px;font-style:italic;">
                    Admins sehen immer alle Hosts
                  </span>
                  <div v-else class="host-checkboxes">
                    <label
                      v-for="h in availableHosts"
                      :key="h.name"
                      class="host-check"
                    >
                      <input
                        type="checkbox"
                        :value="h.name"
                        v-model="editingUser.hosts"
                      />
                      <span>{{ h.display_name || h.name }}</span>
                    </label>
                    <span v-if="availableHosts.length === 0" class="text-muted" style="font-size:11px;">
                      Keine Hosts in den
                      <router-link to="/settings" style="color:var(--ks-500);">Einstellungen</router-link>
                      konfiguriert
                    </span>
                    <label class="host-check host-check-all" v-if="availableHosts.length > 0">
                      <input
                        type="checkbox"
                        :checked="editingUser.hosts.length === 0"
                        @change="editingUser.hosts = []"
                      />
                      <span style="font-style:italic;">Alle (kein Filter)</span>
                    </label>
                  </div>
                </template>
                <template v-else>
                  <span v-if="u.role === 'admin'" class="text-muted" style="font-size:11px;font-style:italic;">Alle (Admin)</span>
                  <div v-else-if="u.hosts.length" class="host-tags">
                    <span v-for="h in u.hosts" :key="h" class="badge badge-gray" style="font-size:10px;font-family:monospace;">{{ h }}</span>
                  </div>
                  <span v-else class="text-muted" style="font-size:11px;font-style:italic;">Alle</span>
                </template>
              </td>

              <td>
                <div class="td-actions">
                  <template v-if="editingUser?.username === u.username">
                    <input
                      type="password"
                      v-model="editingUser.password"
                      class="input input-sm"
                      placeholder="Neues Passwort"
                      style="width:120px;"
                    />
                    <button class="btn btn-primary btn-sm" @click="saveEdit" :disabled="saving">Speichern</button>
                    <button class="btn btn-ghost btn-sm" @click="cancelEdit" :disabled="saving">&#10005;</button>
                  </template>
                  <template v-else>
                    <button class="btn btn-ghost btn-sm" @click="startEdit(u)">Bearbeiten</button>
                    <button
                      class="btn btn-danger btn-sm"
                      @click="deleteUser(u.username)"
                      :disabled="saving || u.username === currentUsername"
                      :title="u.username === currentUsername ? 'Eigenen Account nicht löschbar' : ''"
                    >Löschen</button>
                  </template>
                </div>
              </td>
            </tr>
          </template>

          <tr v-if="!users.length">
            <td colspan="5" class="text-muted" style="text-align:center;padding:20px;">Keine Benutzer gefunden.</td>
          </tr>
        </tbody>
      </table>

      <!-- New user row -->
      <div class="card-body" style="border-top:1px solid var(--border-soft);">
        <div style="font-size:12px;font-weight:600;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em;">Neuer Benutzer</div>
        <div class="new-row">
          <input v-model="newUser.username" class="input" placeholder="Benutzername" />
          <input v-model="newUser.password" type="password" class="input" placeholder="Passwort" />
          <input v-model="newUser.email" type="email" class="input" placeholder="E-Mail (optional)" />
          <select v-model="newUser.role" class="select-inline">
            <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
          </select>
          <button
            class="btn btn-primary btn-sm"
            @click="createUser"
            :disabled="saving || !newUser.username || !newUser.password"
          >Anlegen</button>
        </div>
        <div v-if="availableHosts.length" style="margin-top:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span style="font-size:12px;color:var(--text-muted);">Hosts:</span>
          <label v-for="h in availableHosts" :key="h.name" class="host-check">
            <input type="checkbox" :value="h.name" v-model="newUser.hosts" />
            <span>{{ h.display_name || h.name }}</span>
          </label>
          <span class="text-muted" style="font-size:11px;">(leer = alle)</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

interface UserEntry   { username: string; role: string; email: string; hosts: string[]; }
interface HostEntry   { name: string; display_name: string; ip: string; }
interface EditState   { username: string; role: string; password: string; email: string; hosts: string[]; }

const auth = useAuthStore();
const currentUsername = auth.user?.username ?? '';
const roles = ['admin', 'operator', 'viewer'];

const users          = ref<UserEntry[]>([]);
const availableHosts = ref<HostEntry[]>([]);
const error          = ref('');
const successMsg     = ref('');
const saving         = ref(false);

const editingUser = ref<EditState | null>(null);
const newUser     = ref({ username: '', password: '', role: 'viewer', email: '', hosts: [] as string[] });

function roleBadge(role: string) {
  return { admin: 'badge-blue', operator: 'badge-yellow', viewer: 'badge-gray' }[role] ?? 'badge-gray';
}

function flash(msg: string) {
  successMsg.value = msg;
  setTimeout(() => { successMsg.value = ''; }, 3500);
}

async function loadUsers() {
  error.value = '';
  try {
    const [uRes, hRes] = await Promise.all([
      apiClient.get('/users'),
      apiClient.get('/settings/hosts'),
    ]);
    users.value = uRes.data;
    availableHosts.value = hRes.data;
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Daten konnten nicht geladen werden.';
  }
}

function startEdit(u: UserEntry) {
  editingUser.value = {
    username: u.username,
    role: u.role,
    password: '',
    email: u.email,
    hosts: [...(u.hosts ?? [])],
  };
}

function cancelEdit() { editingUser.value = null; }

async function saveEdit() {
  if (!editingUser.value) return;
  saving.value = true;
  error.value  = '';
  try {
    const payload: Record<string, unknown> = {
      role: editingUser.value.role,
      email: editingUser.value.email,
      hosts: editingUser.value.hosts,
    };
    if (editingUser.value.password) payload.password = editingUser.value.password;
    await apiClient.put(`/users/${editingUser.value.username}`, payload);
    editingUser.value = null;
    flash('Benutzer aktualisiert.');
    await loadUsers();
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Aktualisierung fehlgeschlagen.';
  } finally {
    saving.value = false;
  }
}

async function deleteUser(username: string) {
  if (!confirm(`Benutzer „${username}" wirklich löschen?`)) return;
  saving.value = true;
  error.value  = '';
  try {
    await apiClient.delete(`/users/${username}`);
    flash(`Benutzer „${username}" gelöscht.`);
    await loadUsers();
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Löschen fehlgeschlagen.';
  } finally {
    saving.value = false;
  }
}

async function createUser() {
  saving.value = true;
  error.value  = '';
  try {
    await apiClient.post('/users', { ...newUser.value });
    newUser.value = { username: '', password: '', role: 'viewer', email: '', hosts: [] };
    flash('Benutzer angelegt.');
    await loadUsers();
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Anlegen fehlgeschlagen.';
  } finally {
    saving.value = false;
  }
}

onMounted(loadUsers);
</script>

<style scoped>
.mb-5 { margin-bottom: 20px; }
.row-editing td { background: var(--ks-50); }

.host-checkboxes {
  display: flex; flex-direction: column; gap: 4px; min-width: 140px; max-height: 140px;
  overflow-y: auto; padding: 4px;
}
.host-check {
  display: flex; align-items: center; gap: 5px; font-size: 12px; cursor: pointer;
  white-space: nowrap;
}
.host-check input[type=checkbox] { width: 13px; height: 13px; accent-color: var(--ks-500); }
.host-check-all { margin-top: 4px; border-top: 1px solid var(--border-soft); padding-top: 4px; }

.host-tags { display: flex; gap: 4px; flex-wrap: wrap; }
</style>

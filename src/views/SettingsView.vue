<template>
  <div>
    <div class="page-header">
      <div class="page-header-title">
        <h1>Einstellungen</h1>
        <p>Hosts, Log-Weiterleitung, E-Mail-Alerts und Wartungsfenster</p>
      </div>
    </div>

    <div v-if="message" :class="['alert', msgType === 'error' ? 'alert-error' : 'alert-success']"
         style="margin-bottom:16px;">
      {{ message }}
    </div>

    <!-- ── Tab Bar ───────────────────────────────────────────────────────────── -->
    <div class="tab-bar">
      <button :class="['tab-btn', { active: tab === 'hosts' }]"       @click="tab = 'hosts'">
        <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
        </svg>
        Hosts
      </button>
      <button :class="['tab-btn', { active: tab === 'forwarding' }]"  @click="tab = 'forwarding'">
        <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
        Weiterleitung
      </button>
      <button :class="['tab-btn', { active: tab === 'rotation' }]"    @click="tab = 'rotation'">
        <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/>
        </svg>
        Archivierung
      </button>
      <button :class="['tab-btn', { active: tab === 'email' }]"       @click="tab = 'email'">
        <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
          <polyline points="22,6 12,13 2,6"/>
        </svg>
        E-Mail-Alerts
      </button>
      <button :class="['tab-btn', { active: tab === 'maintenance' }]" @click="tab = 'maintenance'">
        <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>
        </svg>
        Wartung
      </button>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: Hosts                                                            -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <div v-if="tab === 'hosts'" class="card">
      <div class="card-header">
        <span>Hosts verwalten ({{ hosts.length }})</span>
        <button class="btn btn-secondary btn-sm" @click="showAddHost = !showAddHost">
          {{ showAddHost ? 'Abbrechen' : '+ Host hinzufügen' }}
        </button>
      </div>

      <!-- Add-form -->
      <div v-if="showAddHost" class="card-body add-host-form">
        <div class="settings-grid" style="align-items:flex-end;">
          <div class="form-group">
            <label>Hostname *</label>
            <input class="input" v-model="newHost.name" placeholder="server01"
                   @keyup.enter="addHost" />
          </div>
          <div class="form-group">
            <label>Anzeigename</label>
            <input class="input" v-model="newHost.display_name" placeholder="Produktions-Server 1"
                   @keyup.enter="addHost" />
          </div>
          <div class="form-group">
            <label>IP-Adresse</label>
            <input class="input" v-model="newHost.ip" placeholder="192.168.1.10"
                   @keyup.enter="addHost" />
          </div>
          <div style="display:flex;gap:8px;padding-bottom:1px;">
            <button class="btn btn-primary btn-sm" @click="addHost" :disabled="!newHost.name.trim()">
              Hinzufügen
            </button>
          </div>
        </div>
      </div>

      <!-- Host table -->
      <div v-if="hosts.length === 0 && !showAddHost" class="card-body text-muted"
           style="font-size:13px;">
        Keine Hosts registriert. Hosts werden für die Zugriffssteuerung und E-Mail-Alerts benötigt.
      </div>

      <table v-if="hosts.length" class="data-table">
        <thead>
          <tr>
            <th>Hostname</th>
            <th>Anzeigename</th>
            <th>IP-Adresse</th>
            <th style="width:160px;"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in hosts" :key="h.name"
              :class="{ 'row-editing': editingHost?.name === h.name }">

            <!-- Display mode -->
            <template v-if="editingHost?.name !== h.name">
              <td class="font-mono" style="font-size:13px;">{{ h.name }}</td>
              <td>{{ h.display_name || '—' }}</td>
              <td class="text-muted font-mono" style="font-size:12px;">{{ h.ip || '—' }}</td>
              <td>
                <div class="td-actions">
                  <button class="btn btn-ghost btn-sm" @click="startEditHost(h)">Bearbeiten</button>
                  <button class="btn btn-danger btn-sm" @click="deleteHost(h.name)">Entfernen</button>
                </div>
              </td>
            </template>

            <!-- Edit mode -->
            <template v-else>
              <td class="font-mono" style="font-size:13px;color:var(--text-muted);">{{ h.name }}</td>
              <td>
                <input class="input input-sm" v-model="editingHost.display_name"
                       placeholder="Anzeigename" @keyup.enter="saveHost" @keyup.escape="cancelEditHost" />
              </td>
              <td>
                <input class="input input-sm" v-model="editingHost.ip"
                       placeholder="10.x.x.x" @keyup.enter="saveHost" @keyup.escape="cancelEditHost" />
              </td>
              <td>
                <div class="td-actions">
                  <button class="btn btn-primary btn-sm" @click="saveHost" :disabled="savingHost">
                    {{ savingHost ? '…' : 'Speichern' }}
                  </button>
                  <button class="btn btn-ghost btn-sm" @click="cancelEditHost">✕</button>
                </div>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: Forwarding                                                       -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <div v-if="tab === 'forwarding'" class="card">
      <div class="card-header">
        <span>Log-Weiterleitung (Forwarding)</span>
        <label class="toggle-label">
          <input type="checkbox" v-model="fwd.enabled" :disabled="!canEdit" />
          <span class="toggle-track"><span class="toggle-thumb" /></span>
          <span class="toggle-text">{{ fwd.enabled ? 'Aktiv' : 'Deaktiviert' }}</span>
        </label>
      </div>
      <div class="card-body">
        <p class="text-muted text-sm mb-3">
          Alle Logs per TCP oder UDP an einen weiteren Syslog-Server weiterleiten.
        </p>
        <div class="settings-grid" :class="{ 'settings-disabled': !fwd.enabled }">
          <div class="form-group">
            <label>Protokoll</label>
            <select class="input" v-model="fwd.protocol" :disabled="!canEdit || !fwd.enabled">
              <option value="tcp">TCP (@@)</option>
              <option value="udp">UDP (@)</option>
            </select>
          </div>
          <div class="form-group" style="flex:2">
            <label>Ziel-Host / IP</label>
            <input class="input" v-model="fwd.host" placeholder="10.124.40.110"
                   :disabled="!canEdit || !fwd.enabled" />
          </div>
          <div class="form-group">
            <label>Port</label>
            <input class="input" type="number" v-model.number="fwd.port" min="1" max="65535"
                   :disabled="!canEdit || !fwd.enabled" />
          </div>
        </div>
        <div v-if="fwd.enabled && fwd.host" class="preview-line">
          Erzeugt: <code>*.* {{ fwd.protocol === 'tcp' ? '@@' : '@' }}{{ fwd.host }}:{{ fwd.port }}</code>
        </div>
        <div class="action-row">
          <button class="btn btn-primary btn-sm" @click="saveFwd" :disabled="!canEdit || savingFwd">
            {{ savingFwd ? 'Speichert …' : 'Speichern' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: Archivierung / Rotation                                          -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <div v-if="tab === 'rotation'" class="card">
      <div class="card-header">
        <span>Log-Archivierung &amp; Rotation</span>
        <label class="toggle-label">
          <input type="checkbox" v-model="rotation.enabled" :disabled="!canEdit" />
          <span class="toggle-track"><span class="toggle-thumb" /></span>
          <span class="toggle-text">{{ rotation.enabled ? 'Aktiv' : 'Deaktiviert' }}</span>
        </label>
      </div>
      <div class="card-body">
        <p class="text-muted text-sm mb-3">
          Konfiguriert <code>/etc/logrotate.d/rsyslog-remote</code>. Logs pro Host:
          <code>{{ rotation.log_base_dir }}/HOSTNAME/YYYY/MM/</code>
        </p>
        <div :class="{ 'settings-disabled': !rotation.enabled }">
          <div class="settings-grid mb-3">
            <div class="form-group" style="flex:3;">
              <label>Basis-Verzeichnis</label>
              <input class="input" v-model="rotation.log_base_dir" placeholder="/data/syslog"
                     :disabled="!canEdit || !rotation.enabled" />
            </div>
            <div class="form-group">
              <label>Intervall</label>
              <select class="input" v-model="rotation.rotate_interval"
                      :disabled="!canEdit || !rotation.enabled">
                <option value="daily">täglich</option>
                <option value="weekly">wöchentlich</option>
                <option value="monthly">monatlich</option>
              </select>
            </div>
            <div class="form-group">
              <label>Aufbewahrung</label>
              <input class="input" type="number" v-model.number="rotation.rotate_count" min="1" max="120"
                     :disabled="!canEdit || !rotation.enabled" />
            </div>
            <div class="form-group">
              <label>Max. Größe (MB)</label>
              <input class="input" type="number" v-model.number="rotation.max_size_mb" min="0"
                     placeholder="0 = kein Limit" :disabled="!canEdit || !rotation.enabled" />
            </div>
          </div>
          <div class="checkbox-row mb-3">
            <label class="cb-label">
              <input type="checkbox" v-model="rotation.compress" :disabled="!canEdit || !rotation.enabled" />
              Komprimieren (gzip)
            </label>
            <label class="cb-label">
              <input type="checkbox" v-model="rotation.date_ext" :disabled="!canEdit || !rotation.enabled" />
              Datum im Dateinamen
            </label>
          </div>
        </div>

        <details style="margin-bottom:14px;">
          <summary class="snippet-toggle">rsyslog-Template anzeigen</summary>
          <pre class="snippet-box">{{ rsyslogTemplate }}</pre>
          <button class="btn btn-ghost btn-sm" style="margin-top:4px;" @click="copyTemplate">
            📋 In Zwischenablage
          </button>
        </details>

        <div class="action-row">
          <button class="btn btn-primary btn-sm" @click="saveRotation" :disabled="!canEdit || savingRotation">
            {{ savingRotation ? 'Speichert …' : 'Speichern' }}
          </button>
          <button class="btn btn-ghost btn-sm" @click="loadTemplate">Snippet aktualisieren</button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: E-Mail-Alerts                                                    -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <div v-if="tab === 'email'" class="card">
      <div class="card-header">
        <span>E-Mail-Alerts (ommail)</span>
        <label class="toggle-label">
          <input type="checkbox" v-model="email.enabled" :disabled="!canEdit" />
          <span class="toggle-track"><span class="toggle-thumb" /></span>
          <span class="toggle-text">{{ email.enabled ? 'Aktiv' : 'Deaktiviert' }}</span>
        </label>
      </div>
      <div class="card-body">
        <div class="alert alert-info mb-3">
          <svg style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;flex-shrink:0;" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          Empfänger und Host-Filter werden aus der
          <router-link to="/users" style="color:var(--ks-700);font-weight:600;">Benutzerverwaltung</router-link>
          abgeleitet.
        </div>

        <div :class="{ 'settings-disabled': !email.enabled }">
          <div class="settings-grid mb-3">
            <div class="form-group" style="flex:2">
              <label>SMTP-Server</label>
              <input class="input" v-model="email.smtp_server" placeholder="mail-gw.dmz.example.net"
                     :disabled="!canEdit || !email.enabled" />
            </div>
            <div class="form-group">
              <label>SMTP-Port</label>
              <input class="input" type="number" v-model.number="email.smtp_port"
                     :disabled="!canEdit || !email.enabled" />
            </div>
          </div>
          <div class="settings-grid mb-3">
            <div class="form-group">
              <label>Absender (From)</label>
              <input class="input" type="email" v-model="email.mail_from" placeholder="syslog@example.net"
                     :disabled="!canEdit || !email.enabled" />
            </div>
            <div class="form-group">
              <label>Min. Schweregrad</label>
              <select class="input" v-model.number="email.min_severity"
                      :disabled="!canEdit || !email.enabled">
                <option :value="0">0 — emerg</option>
                <option :value="1">1 — alert</option>
                <option :value="2">2 — crit</option>
                <option :value="3">3 — err</option>
                <option :value="4">4 — warning</option>
                <option :value="5">5 — notice</option>
                <option :value="6">6 — info</option>
              </select>
            </div>
            <div class="form-group">
              <label>Throttle (Sek.)</label>
              <input class="input" type="number" v-model.number="email.throttle_interval" min="60"
                     :disabled="!canEdit || !email.enabled" />
            </div>
          </div>

          <div v-if="email.enabled && alertUsers.length > 0" class="mb-3">
            <div class="section-label mb-2">Aktive Alert-Regeln</div>
            <div class="alert-rules">
              <div v-for="u in alertUsers" :key="u.username" class="alert-rule-row">
                <span class="badge badge-blue font-mono">{{ u.username }}</span>
                <svg style="width:14px;height:14px;stroke:var(--text-muted);fill:none;stroke-width:2;flex-shrink:0;" viewBox="0 0 24 24">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
                <span class="text-muted" style="font-size:12px;">{{ u.email }}</span>
                <span class="text-muted" style="font-size:11px;margin-left:4px;">
                  {{ u.hosts.length ? `(${u.hosts.join(', ')})` : '(alle Hosts)' }}
                </span>
              </div>
            </div>
          </div>
          <div v-else-if="email.enabled" class="text-muted text-sm mb-3">
            Keine Benutzer mit E-Mail-Adresse.
            <router-link to="/users" style="color:var(--ks-500);">Jetzt konfigurieren →</router-link>
          </div>
        </div>

        <div class="action-row">
          <button class="btn btn-primary btn-sm" @click="saveEmail" :disabled="!canEdit || savingEmail">
            {{ savingEmail ? 'Speichert …' : 'Speichern' }}
          </button>
          <button class="btn btn-ghost btn-sm" @click="regenerateEmail" :disabled="!canEdit">
            Neu generieren
          </button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: Wartungsfenster                                                  -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <div v-if="tab === 'maintenance'" class="card">
      <div class="card-header">
        <span>Wartungsfenster / Alert-Pause</span>
        <label class="toggle-label">
          <input type="checkbox" v-model="maint.enabled" :disabled="!canEdit" />
          <span class="toggle-track"><span class="toggle-thumb" /></span>
          <span class="toggle-text">{{ maint.enabled ? 'Aktiv' : 'Inaktiv' }}</span>
        </label>
      </div>
      <div class="card-body" :class="{ 'settings-disabled': !maint.enabled }">

        <!-- Manual pause banner -->
        <div class="maint-pause-row mb-3">
          <div>
            <div class="section-label">Manuelle Pause</div>
            <div style="margin-top:4px;font-size:13px;">
              <span v-if="maint.pause_until && isPaused" class="badge badge-warn">
                Aktiv bis {{ formatPauseUntil(maint.pause_until) }}
              </span>
              <span v-else class="text-muted" style="font-size:12px;">Keine aktive Pause</span>
            </div>
          </div>
          <div v-if="canEdit" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <select v-model="pauseHours" class="input" style="width:80px;">
              <option :value="1">1 h</option>
              <option :value="2">2 h</option>
              <option :value="4">4 h</option>
              <option :value="8">8 h</option>
              <option :value="24">24 h</option>
            </select>
            <button class="btn btn-secondary btn-sm" @click="pauseAlerts" :disabled="savingMaint">
              Pause starten
            </button>
            <button v-if="isPaused" class="btn btn-ghost btn-sm" @click="resumeAlerts"
                    :disabled="savingMaint">Beenden</button>
          </div>
        </div>

        <div class="section-label mb-2">Zeitfenster (wiederkehrend)</div>
        <div v-if="!maint.windows.length" class="text-muted text-sm mb-3">Keine Fenster definiert.</div>

        <div v-for="(w, idx) in maint.windows" :key="idx" class="maint-window-row">
          <input v-model="w.start" type="time" class="input" style="width:100px;" :disabled="!canEdit" />
          <span class="text-muted">–</span>
          <input v-model="w.end"   type="time" class="input" style="width:100px;" :disabled="!canEdit" />
          <div class="day-toggles">
            <label v-for="(d, di) in ['Mo','Di','Mi','Do','Fr','Sa','So']" :key="di" class="day-toggle">
              <input type="checkbox" :value="di" v-model="w.days" :disabled="!canEdit" />
              <span>{{ d }}</span>
            </label>
          </div>
          <button v-if="canEdit" class="btn btn-ghost btn-sm" @click="removeWindow(idx)">✕</button>
        </div>

        <div v-if="canEdit" class="action-row" style="gap:8px;margin-top:12px;">
          <button class="btn btn-ghost btn-sm" @click="addWindow">+ Fenster hinzufügen</button>
          <button class="btn btn-primary btn-sm" @click="saveMaint" :disabled="savingMaint">
            {{ savingMaint ? 'Speichert …' : 'Speichern' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { apiClient } from '../api';

interface HostEntry  { name: string; display_name: string; ip: string; }
interface AlertUser  { username: string; email: string; hosts: string[]; }
interface MaintWindow { name: string; start: string; end: string; days: number[]; }

const auth    = useAuthStore();
const canEdit = computed(() => auth.isAdmin || auth.isOperator);

const tab     = ref<'hosts' | 'forwarding' | 'rotation' | 'email' | 'maintenance'>('hosts');
const message = ref('');
const msgType = ref<'success' | 'error'>('success');

function flash(msg: string, type: 'success' | 'error' = 'success') {
  message.value = msg; msgType.value = type;
  setTimeout(() => { message.value = ''; }, 4000);
}

// ── Hosts ──────────────────────────────────────────────────────────────────
const hosts       = ref<HostEntry[]>([]);
const showAddHost = ref(false);
const newHost     = ref<HostEntry>({ name: '', display_name: '', ip: '' });
const editingHost = ref<HostEntry | null>(null);
const savingHost  = ref(false);

function startEditHost(h: HostEntry) {
  editingHost.value = { ...h };
}
function cancelEditHost() { editingHost.value = null; }

async function saveHost() {
  if (!editingHost.value) return;
  savingHost.value = true;
  try {
    await apiClient.put(`/settings/hosts/${editingHost.value.name}`, {
      name: editingHost.value.name,
      display_name: editingHost.value.display_name,
      ip: editingHost.value.ip,
    });
    editingHost.value = null;
    flash('Host aktualisiert.');
    const res = await apiClient.get('/settings/hosts');
    hosts.value = res.data;
  } catch (e: any) {
    flash(e.response?.data?.detail ?? 'Fehler beim Speichern.', 'error');
  } finally { savingHost.value = false; }
}

async function addHost() {
  if (!newHost.value.name.trim()) return;
  try {
    await apiClient.post('/settings/hosts', { ...newHost.value });
    showAddHost.value = false;
    newHost.value = { name: '', display_name: '', ip: '' };
    flash('Host hinzugefügt.');
    const res = await apiClient.get('/settings/hosts');
    hosts.value = res.data;
  } catch (e: any) {
    flash(e.response?.data?.detail ?? 'Fehler beim Hinzufügen.', 'error');
  }
}

async function deleteHost(name: string) {
  if (!confirm(`Host "${name}" wirklich entfernen?`)) return;
  try {
    await apiClient.delete(`/settings/hosts/${name}`);
    flash(`Host "${name}" entfernt.`);
    const res = await apiClient.get('/settings/hosts');
    hosts.value = res.data;
  } catch (e: any) {
    flash(e.response?.data?.detail ?? 'Fehler.', 'error');
  }
}

// ── Forwarding ─────────────────────────────────────────────────────────────
const fwd       = reactive({ enabled: false, protocol: 'tcp', host: '', port: 514 });
const savingFwd = ref(false);

async function saveFwd() {
  savingFwd.value = true;
  try {
    await apiClient.put('/settings/forwarding', { ...fwd });
    flash('Forwarding gespeichert.');
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { savingFwd.value = false; }
}

// ── Rotation ───────────────────────────────────────────────────────────────
const rotation = reactive({
  enabled: true, log_base_dir: '/data/syslog', rotate_count: 12,
  rotate_interval: 'monthly', compress: true, max_size_mb: 0, date_ext: true,
});
const rsyslogTemplate = ref('');
const savingRotation  = ref(false);

async function loadTemplate() {
  try {
    const res = await apiClient.get('/settings/rsyslog-template');
    rsyslogTemplate.value = res.data.template ?? '';
  } catch { /* ignore */ }
}

async function copyTemplate() {
  try {
    await navigator.clipboard.writeText(rsyslogTemplate.value);
    flash('Template in Zwischenablage kopiert.');
  } catch { flash('Kopieren fehlgeschlagen.', 'error'); }
}

async function saveRotation() {
  savingRotation.value = true;
  try {
    await apiClient.put('/settings/rotation', { ...rotation });
    await loadTemplate();
    flash('Archivierungs-Einstellungen gespeichert.');
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { savingRotation.value = false; }
}

// ── Email ──────────────────────────────────────────────────────────────────
const email = reactive({
  enabled: false, smtp_server: '', smtp_port: 25,
  mail_from: '', min_severity: 4, throttle_interval: 300,
});
const alertUsers  = ref<AlertUser[]>([]);
const savingEmail = ref(false);

async function saveEmail() {
  savingEmail.value = true;
  try {
    await apiClient.put('/settings/email', { ...email });
    flash('E-Mail-Einstellungen gespeichert.');
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { savingEmail.value = false; }
}

async function regenerateEmail() {
  try {
    await apiClient.post('/settings/email/regenerate');
    flash('E-Mail-Konfiguration neu generiert.');
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
}

// ── Maintenance ────────────────────────────────────────────────────────────
const maint = reactive<{ enabled: boolean; windows: MaintWindow[]; pause_until: string | null }>({
  enabled: false, windows: [], pause_until: null,
});
const savingMaint = ref(false);
const pauseHours  = ref(2);
const isPaused    = computed(() => {
  if (!maint.pause_until) return false;
  try { return new Date(maint.pause_until) > new Date(); } catch { return false; }
});

function formatPauseUntil(iso: string) {
  try { return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }); }
  catch { return iso; }
}

function addWindow()           { maint.windows.push({ name: '', start: '22:00', end: '06:00', days: [0,1,2,3,4,5,6] }); }
function removeWindow(i: number) { maint.windows.splice(i, 1); }

async function saveMaint() {
  savingMaint.value = true;
  try {
    await apiClient.put('/settings/maintenance', { ...maint });
    flash('Wartungsfenster gespeichert.');
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { savingMaint.value = false; }
}

async function pauseAlerts() {
  savingMaint.value = true;
  try {
    const res = await apiClient.post('/settings/maintenance/pause', { hours: pauseHours.value });
    maint.enabled = true;
    maint.pause_until = res.data.pause_until;
    flash(`Alerts pausiert für ${pauseHours.value} h.`);
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { savingMaint.value = false; }
}

async function resumeAlerts() {
  savingMaint.value = true;
  try {
    await apiClient.post('/settings/maintenance/resume');
    maint.pause_until = null;
    flash('Pause beendet — Alerts aktiv.');
  } catch (e: any) { flash(e.response?.data?.detail ?? 'Fehler.', 'error'); }
  finally { savingMaint.value = false; }
}

// ── Load all ───────────────────────────────────────────────────────────────
async function loadAll() {
  try {
    const [h, f, e, u, r, m] = await Promise.all([
      apiClient.get('/settings/hosts'),
      apiClient.get('/settings/forwarding'),
      apiClient.get('/settings/email'),
      apiClient.get('/users'),
      apiClient.get('/settings/rotation'),
      apiClient.get('/settings/maintenance'),
    ]);
    hosts.value = h.data;
    Object.assign(fwd, f.data);
    Object.assign(email, e.data);
    alertUsers.value = (u.data as AlertUser[]).filter(u => u.email);
    Object.assign(rotation, r.data);
    Object.assign(maint, m.data);
    await loadTemplate();
  } catch { flash('Daten konnten nicht geladen werden.', 'error'); }
}

onMounted(loadAll);
</script>

<style scoped>
/* ── Tab bar ─────────────────────────────────────────────────────────────── */
.tab-bar {
  display: flex;
  gap: 2px;
  border-bottom: 2px solid var(--border);
  margin-bottom: 20px;
  overflow-x: auto;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  white-space: nowrap;
  transition: color .15s, border-color .15s;
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--ks-600); border-bottom-color: var(--ks-500); }
.tab-icon {
  width: 15px; height: 15px; flex-shrink: 0;
}

/* ── Misc layout ─────────────────────────────────────────────────────────── */
.mb-3 { margin-bottom: 12px; }
.font-mono { font-family: ui-monospace, monospace; }
.text-sm   { font-size: 13px; }
.section-label { font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .05em; color: var(--text-muted); }

.settings-grid { display: flex; gap: 12px; flex-wrap: wrap; }
.settings-grid .form-group { flex: 1; min-width: 150px; }
.settings-disabled { opacity: .45; pointer-events: none; }

.add-host-form { border-bottom: 1px solid var(--border-soft); background: var(--ks-50); }

.row-editing td { background: var(--ks-50); }
.input-sm { padding: 4px 8px; font-size: 12px; }

.td-actions { display: flex; gap: 6px; }

.checkbox-row { display: flex; gap: 20px; flex-wrap: wrap; }
.cb-label { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
.cb-label input[type=checkbox] { accent-color: var(--ks-500); }

.preview-line {
  margin: 12px 0;
  padding: 8px 12px;
  background: var(--ks-50);
  border: 1px solid var(--ks-200);
  border-radius: 6px;
  font-size: 12px;
  color: var(--ks-700);
}
.preview-line code { font-family: ui-monospace, monospace; font-weight: 600; }

.snippet-toggle {
  font-size: 12px; color: var(--ks-600); cursor: pointer; user-select: none;
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
  max-height: 260px;
  overflow-y: auto;
}

.alert-rules { display: flex; flex-direction: column; gap: 6px; }
.alert-rule-row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
}

/* Toggle */
.toggle-label { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; }
.toggle-label input { display: none; }
.toggle-track {
  position: relative; display: inline-block; width: 36px; height: 20px;
  background: #cbd5e1; border-radius: 999px; transition: background .2s; flex-shrink: 0;
}
.toggle-label input:checked + .toggle-track { background: var(--ks-500); }
.toggle-thumb {
  position: absolute; top: 2px; left: 2px; width: 16px; height: 16px;
  background: #fff; border-radius: 50%; transition: left .2s; box-shadow: 0 1px 3px rgba(0,0,0,.2);
}
.toggle-label input:checked + .toggle-track .toggle-thumb { left: 18px; }
.toggle-text { font-size: 12px; font-weight: 400; color: var(--text-muted); }

/* Maintenance */
.maint-pause-row {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 12px;
  padding: 14px; background: var(--bg);
  border: 1px solid var(--border); border-radius: 8px;
}
.maint-window-row {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 8px; background: var(--bg);
  border: 1px solid var(--border); border-radius: 6px; margin-bottom: 6px;
}
.day-toggles { display: flex; gap: 4px; }
.day-toggle {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  font-size: 10px; font-weight: 500; cursor: pointer; color: var(--text-muted);
}
.day-toggle input[type=checkbox] { accent-color: var(--ks-500); }
.day-toggle input:checked + span { color: var(--ks-700); font-weight: 700; }

.badge-warn {
  background: #fef9c3; color: #78350f;
  font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 9px;
}
</style>

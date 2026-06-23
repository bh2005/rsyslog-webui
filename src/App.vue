<template>
  <!-- Login page: full-screen, no sidebar -->
  <router-view v-if="route.meta.public" />

  <!-- App shell with left sidebar -->
  <div v-else class="app-layout">
    <aside class="app-sidebar">

      <!-- Header -->
      <div class="sidebar-header">
        <div class="sidebar-brand">
          <div class="sidebar-brand-name">RSYSLOG Manager</div>
          <div class="sidebar-brand-sub">Log Management</div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <router-link class="nav-link" to="/" exact>
          <svg class="nav-icon" viewBox="0 0 24 24">
            <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
          </svg>
          Dashboard
        </router-link>

        <router-link class="nav-link" to="/receiver">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
          Receiver
        </router-link>

        <router-link class="nav-link" to="/my-hosts">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3"/>
            <path d="M9 21v-6a2 2 0 012-2h2a2 2 0 012 2v6"/>
          </svg>
          Meine Hosts
        </router-link>

        <router-link class="nav-link" to="/logs">
          <svg class="nav-icon" viewBox="0 0 24 24">
            <path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
          </svg>
          Logs
        </router-link>

        <router-link class="nav-link" to="/stats">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          Monitoring
        </router-link>

        <router-link class="nav-link" to="/logfiles">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            <path d="M8 2v3M16 2v3M3 11h18"/>
            <path d="M8 15h.01M12 15h.01M16 15h.01"/>
          </svg>
          Log-Dateien
        </router-link>

        <router-link class="nav-link" to="/manuals">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
          </svg>
          Handbücher
        </router-link>

        <template v-if="isAdmin">
          <hr class="sidebar-divider" />
          <div class="sidebar-section-label">Administration</div>

          <router-link class="nav-link" to="/config">
            <svg class="nav-icon" viewBox="0 0 24 24">
              <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            Konfiguration
          </router-link>

          <router-link class="nav-link" to="/users">
            <svg class="nav-icon" viewBox="0 0 24 24">
              <path d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
            Benutzer
          </router-link>

          <router-link class="nav-link" to="/groups">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
            </svg>
            Gruppen
          </router-link>

          <router-link class="nav-link" to="/audit">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
            Audit-Log
          </router-link>

          <router-link class="nav-link" to="/syslogs">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2"/>
              <path d="M8 21h8M12 17v4"/>
              <path d="M7 8h.01M7 12h.01M11 8l4 0M11 12l6 0"/>
            </svg>
            System-Logs
          </router-link>

          <router-link class="nav-link" to="/settings">
            <svg class="nav-icon" viewBox="0 0 24 24">
              <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
              <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            Einstellungen
          </router-link>
        </template>
      </nav>

      <!-- Footer: user info + logout + help -->
      <div class="sidebar-footer">
        <div class="sidebar-user">
          <div class="sidebar-user-info" style="cursor:pointer;" @click="openProfileModal" title="Mein Profil">
            <div class="sidebar-username">{{ user?.username }}</div>
            <div class="sidebar-role">{{ user?.role }} <span style="font-size:9px;opacity:.5;">⚙</span></div>
          </div>
          <button class="btn-icon" title="Hilfe (F1)" @click="helpOpen = !helpOpen" style="font-size:15px;font-weight:700;">?</button>
          <button class="btn-icon" title="Abmelden" @click="logout">
            <svg viewBox="0 0 24 24">
              <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- ── Profil-Modal ───────────────────────────────────────────────────── -->
    <div v-if="showPwModal" class="pw-overlay" @click.self="closePwModal">
      <div class="pw-modal">
        <div class="pw-header">
          <span>Mein Profil</span>
          <button class="pw-close" @click="closePwModal">✕</button>
        </div>
        <div class="pw-body">

          <!-- User identity -->
          <div class="pw-identity">
            <div class="pw-avatar">{{ user?.username?.[0]?.toUpperCase() }}</div>
            <div>
              <div class="pw-identity-name">{{ user?.username }}</div>
              <span class="badge" :class="roleBadgeClass">{{ user?.role }}</span>
            </div>
          </div>

          <!-- E-Mail -->
          <div class="pw-section-title">E-Mail-Adresse</div>
          <div v-if="profileMsg" :class="['pw-alert', profileMsgType === 'error' ? 'pw-error' : 'pw-ok']">{{ profileMsg }}</div>
          <div class="pw-field">
            <label>E-Mail</label>
            <input v-model="profileForm.email" type="email" class="form-input" placeholder="name@beispiel.de" />
          </div>
          <div style="display:flex;justify-content:flex-end;margin-top:4px;">
            <button class="btn btn-primary btn-sm" @click="saveProfile" :disabled="profileSaving">
              {{ profileSaving ? 'Wird gespeichert…' : 'E-Mail speichern' }}
            </button>
          </div>

          <hr class="pw-divider" />

          <!-- Passwort ändern -->
          <div class="pw-section-title">Passwort ändern</div>
          <div v-if="pwMsg" :class="['pw-alert', pwMsgType === 'error' ? 'pw-error' : 'pw-ok']">{{ pwMsg }}</div>
          <div class="pw-field">
            <label>Aktuelles Passwort</label>
            <input v-model="pwForm.current" type="password" class="form-input" autocomplete="current-password" />
          </div>
          <div class="pw-field">
            <label>Neues Passwort</label>
            <input v-model="pwForm.next" type="password" class="form-input" autocomplete="new-password" />
          </div>
          <div class="pw-field">
            <label>Neues Passwort bestätigen</label>
            <input v-model="pwForm.confirm" type="password" class="form-input" autocomplete="new-password" />
          </div>
        </div>
        <div class="pw-footer">
          <button class="btn btn-ghost" @click="closePwModal">Schließen</button>
          <button class="btn btn-primary" @click="changePassword" :disabled="pwSaving">
            {{ pwSaving ? 'Wird gespeichert…' : 'Passwort ändern' }}
          </button>
        </div>
      </div>
    </div>

    <main class="app-main">
      <router-view />
    </main>

    <HelpPanel :open="helpOpen" @close="helpOpen = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth';
import { apiClient } from './api';
import HelpPanel from './components/HelpPanel.vue';

const route  = useRoute();
const router = useRouter();
const auth   = useAuthStore();

const user    = computed(() => auth.user);
const isAdmin = computed(() => auth.isAdmin);

function logout() {
  auth.logout();
  router.push({ name: 'Login' });
}

// ── Help panel ─────────────────────────────────────────────────────────────
const helpOpen = ref(false);

function onGlobalKey(e: KeyboardEvent) {
  if (e.key === 'F1') { e.preventDefault(); helpOpen.value = !helpOpen.value; }
  if (e.key === '?' && !(e.target instanceof HTMLInputElement) && !(e.target instanceof HTMLTextAreaElement)) {
    helpOpen.value = !helpOpen.value;
  }
}

onMounted(() => document.addEventListener('keydown', onGlobalKey));
onUnmounted(() => document.removeEventListener('keydown', onGlobalKey));

// ── Profile / password modal ───────────────────────────────────────────────
const showPwModal = ref(false);

const roleBadgeClass = computed(() => ({
  admin: 'badge-blue', operator: 'badge-yellow', viewer: 'badge-gray',
}[user.value?.role ?? ''] ?? 'badge-gray'));

// Profile (email)
const profileSaving  = ref(false);
const profileMsg     = ref('');
const profileMsgType = ref<'success' | 'error'>('success');
const profileForm    = reactive({ email: '' });

async function openProfileModal() {
  showPwModal.value = true;
  profileMsg.value = '';
  try {
    const res = await apiClient.get('/users/me');
    profileForm.email = res.data.email ?? '';
  } catch { /* ignore — modal still opens */ }
}

async function saveProfile() {
  profileMsg.value = '';
  profileSaving.value = true;
  try {
    await apiClient.put('/users/me/profile', { email: profileForm.email });
    profileMsg.value = 'E-Mail gespeichert.';
    profileMsgType.value = 'success';
    setTimeout(() => { profileMsg.value = ''; }, 3000);
  } catch (e: any) {
    profileMsg.value = e.response?.data?.detail ?? 'Fehler beim Speichern.';
    profileMsgType.value = 'error';
  } finally {
    profileSaving.value = false;
  }
}

// Password change
const pwSaving  = ref(false);
const pwMsg     = ref('');
const pwMsgType = ref<'success' | 'error'>('success');
const pwForm    = reactive({ current: '', next: '', confirm: '' });

function closePwModal() {
  showPwModal.value = false;
  pwMsg.value = ''; pwForm.current = ''; pwForm.next = ''; pwForm.confirm = '';
  profileMsg.value = '';
}

async function changePassword() {
  pwMsg.value = '';
  if (!pwForm.current || !pwForm.next) {
    pwMsg.value = 'Alle Felder ausfüllen.'; pwMsgType.value = 'error'; return;
  }
  if (pwForm.next !== pwForm.confirm) {
    pwMsg.value = 'Passwörter stimmen nicht überein.'; pwMsgType.value = 'error'; return;
  }
  if (pwForm.next.length < 6) {
    pwMsg.value = 'Passwort muss mindestens 6 Zeichen haben.'; pwMsgType.value = 'error'; return;
  }
  pwSaving.value = true;
  try {
    await apiClient.put('/users/me/password', {
      current_password: pwForm.current,
      new_password: pwForm.next,
    });
    pwMsg.value = 'Passwort erfolgreich geändert.'; pwMsgType.value = 'success';
    setTimeout(closePwModal, 1500);
  } catch (e: any) {
    pwMsg.value = e.response?.data?.detail ?? 'Fehler beim Ändern des Passworts.';
    pwMsgType.value = 'error';
  } finally {
    pwSaving.value = false;
  }
}
</script>

<style scoped>
/* Password modal */
.pw-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center; z-index: 200; }
.pw-modal { background: white; border-radius: 10px; width: 380px; max-width: 95vw;
  box-shadow: 0 20px 60px rgba(0,0,0,.25); }
.pw-header { display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #e2e8f0; font-weight: 600; font-size: 15px; }
.pw-close { background: none; border: none; cursor: pointer; font-size: 18px; opacity: .5; }
.pw-close:hover { opacity: 1; }
.pw-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 12px; }
.pw-field { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.pw-field label { font-weight: 500; }
.pw-footer { display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px; border-top: 1px solid #e2e8f0; }
.pw-alert { padding: 8px 12px; border-radius: 6px; font-size: 12px; }
.pw-ok    { background: #dcfce7; color: #166534; }
.pw-error { background: #fee2e2; color: #991b1b; }

.pw-identity { display:flex; align-items:center; gap:12px; padding: 4px 0 12px; border-bottom:1px solid #e2e8f0; margin-bottom:12px; }
.pw-avatar { background: var(--ks-500); color: #fff; border-radius: 50%; width: 36px; height: 36px;
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size:16px; flex-shrink:0; }
.pw-identity-name { font-weight: 600; font-size: 14px; margin-bottom: 3px; }
.pw-section-title { font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;
  letter-spacing: .06em; margin-bottom: 8px; }
.pw-divider { border: none; border-top: 1px solid #e2e8f0; margin: 14px 0; }
</style>

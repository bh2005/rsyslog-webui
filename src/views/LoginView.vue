<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-app-title">RSYSLOG Manager</div>
      <div class="login-app-sub">Anmeldung erforderlich</div>

      <form @submit.prevent="submitLogin">
        <div class="form-group">
          <label for="username">Benutzername</label>
          <input
            id="username"
            v-model="username"
            class="input"
            autocomplete="username"
            placeholder="admin"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">Passwort</label>
          <input
            id="password"
            type="password"
            v-model="password"
            class="input"
            autocomplete="current-password"
            required
          />
        </div>

        <div style="margin-top: 6px;">
          <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;" :disabled="loading">
            {{ loading ? 'Anmelden …' : 'Anmelden' }}
          </button>
        </div>
      </form>

      <div class="alert alert-error" style="margin-top:14px;margin-bottom:0;" v-if="error">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router  = useRouter();
const auth    = useAuthStore();
const username = ref('');
const password = ref('');
const error    = ref<string | null>(null);
const loading  = ref(false);

async function submitLogin() {
  error.value   = null;
  loading.value = true;
  try {
    await auth.login(username.value, password.value);
    await router.push({ name: 'Dashboard' });
  } catch (err: any) {
    error.value = auth.error ?? err.message;
  } finally {
    loading.value = false;
  }
}
</script>

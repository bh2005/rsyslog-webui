import { defineStore } from 'pinia';
import { apiClient, setAuthToken } from '../api';

interface UserInfo {
  username: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: UserInfo | null;
  error: string | null;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: localStorage.getItem('auth_token'),
    user: localStorage.getItem('auth_user') ? JSON.parse(localStorage.getItem('auth_user')!) : null,
    error: null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    isAdmin: (state) => state.user?.role === 'admin',
    isOperator: (state) => state.user?.role === 'operator',
  },
  actions: {
    async login(username: string, password: string) {
      this.error = null;
      try {
        const response = await apiClient.post('/auth/login', { username, password });
        const token = response.data.access_token as string;
        const expiresAt = response.data.expires_at as string;
        this.token = token;
        this.user = { username, role: response.data.role ?? 'viewer' };
        localStorage.setItem('auth_token', token);
        localStorage.setItem('auth_user', JSON.stringify(this.user));
        localStorage.setItem('auth_expires_at', expiresAt);
        setAuthToken(token);
      } catch (error: any) {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        this.error = error.response?.data?.detail ?? 'Login failed';
        throw new Error(this.error);
      }
    },
    async fetchCurrentUser() {
      if (!this.token) {
        return;
      }

      try {
        const response = await apiClient.get('/auth/me');
        this.user = response.data as UserInfo;
        localStorage.setItem('auth_user', JSON.stringify(this.user));
      } catch (error: any) {
        this.logout();
      }
    },
    logout() {
      this.token = null;
      this.user = null;
      this.error = null;
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_expires_at');
      setAuthToken(null);
    },
    async initialize() {
      if (this.token) {
        setAuthToken(this.token);
        if (!this.user) {
          await this.fetchCurrentUser();
        }
      }
    },
  },
});

import axios from 'axios';
import { useConnectionStore } from './stores/connection';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => {
    useConnectionStore().reportSuccess();
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_expires_at');
      window.location.href = '/login';
    }
    // Kein response = Netzwerkfehler/Timeout, 5xx = Backend erreichbar aber kaputt
    // -> beides als "offline" werten. Reguläre 4xx (401/403/404/...) heißt die
    // Verbindung steht, das ist kein Verbindungsproblem.
    if (!error.response || error.response.status >= 500) {
      useConnectionStore().reportFailure();
    } else {
      useConnectionStore().reportSuccess();
    }
    return Promise.reject(error);
  },
);

export function setAuthToken(token: string | null) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
}

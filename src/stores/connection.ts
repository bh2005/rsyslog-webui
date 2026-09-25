import { defineStore } from 'pinia';

// Erst nach mehreren aufeinanderfolgenden fehlgeschlagenen Requests als "offline"
// werten, damit ein einzelner kurzer Netz-Blip nicht sofort das Warnbanner auslöst.
const FAILURE_THRESHOLD = 2;

interface ConnectionState {
  online: boolean;
  consecutiveFailures: number;
}

export const useConnectionStore = defineStore('connection', {
  state: (): ConnectionState => ({
    online: true,
    consecutiveFailures: 0,
  }),
  actions: {
    reportSuccess() {
      this.consecutiveFailures = 0;
      this.online = true;
    },
    reportFailure() {
      this.consecutiveFailures += 1;
      if (this.consecutiveFailures >= FAILURE_THRESHOLD) {
        this.online = false;
      }
    },
  },
});

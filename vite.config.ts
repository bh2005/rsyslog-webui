import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'RSYSLOG Manager',
        short_name: 'RSYSLOG',
        description: 'PWA zur Verwaltung eines RSYSLOG Servers auf Debian-Basis',
        theme_color: '#0f172a',
        icons: [
          {
            src: 'icon.svg',
            sizes: '192x192',
            type: 'image/svg+xml'
          }
        ],
        start_url: '/',
        display: 'standalone',
        background_color: '#0f172a'
      }
    })
  ],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});

<template>
  <section class="dashboard">
    <div class="cards">
      <article class="card status-card">
        <h2>Service-Status</h2>
        <p class="status ok">aktiv</p>
        <small>rsyslog läuft auf dem Host.</small>
      </article>

      <article class="card config-card">
        <h2>Konfiguration</h2>
        <p>rsyslog.conf</p>
        <button>Bearbeiten</button>
      </article>

      <article class="card logs-card">
        <h2>Aktuelle Logs</h2>
        <pre>
kern.err: rsyslogd: im Journal gefundene Meldungen
syslog.info: Neue Konfigurationsänderung erkannt
        </pre>
      </article>
    </div>

    <section class="actions">
      <h3>Schnellaktionen</h3>
      <div class="action-grid">
        <button>Service neu starten</button>
        <button>Konfiguration testen</button>
        <button>Logs aktualisieren</button>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts"></script>

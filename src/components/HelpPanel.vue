<template>
  <Teleport to="body">
    <Transition name="help-slide">
      <div v-if="open" class="help-overlay" @click.self="$emit('close')">
        <div class="help-panel">
          <div class="help-header">
            <span class="help-title">Hilfe</span>
            <div style="display:flex;gap:8px;align-items:center;">
              <router-link to="/manuals" class="help-manual-link" @click="$emit('close')">
                Handbuch →
              </router-link>
              <button class="help-close" @click="$emit('close')" title="Schließen (Esc)">✕</button>
            </div>
          </div>
          <div class="help-body" v-html="content"></div>
          <div class="help-footer">
            <span>F1 oder ? zum Öffnen/Schließen</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { getHelp } from '../content/helpTexts';

const props = defineProps<{ open: boolean }>();
const emit  = defineEmits<{ (e: 'close'): void }>();

const route   = useRoute();
const content = computed(() => getHelp(route.path));

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.open) emit('close');
}

onMounted(() => document.addEventListener('keydown', onKey));
onUnmounted(() => document.removeEventListener('keydown', onKey));
</script>

<style scoped>
.help-overlay {
  position: fixed; inset: 0; z-index: 150;
  background: rgba(0,0,0,.3);
}
.help-panel {
  position: fixed; top: 0; right: 0; bottom: 0;
  width: 380px; max-width: 95vw;
  background: #fff;
  box-shadow: -4px 0 24px rgba(0,0,0,.15);
  display: flex; flex-direction: column;
  overflow: hidden;
}
.help-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
  flex-shrink: 0;
}
.help-title {
  font-weight: 700; font-size: 15px; color: #1e293b;
}
.help-manual-link {
  font-size: 12px; color: #3b82f6; text-decoration: none; font-weight: 500;
}
.help-manual-link:hover { text-decoration: underline; }
.help-close {
  background: none; border: none; cursor: pointer;
  font-size: 16px; color: #64748b; padding: 2px 6px; border-radius: 4px;
}
.help-close:hover { background: #f1f5f9; color: #0f172a; }
.help-body {
  flex: 1; overflow-y: auto; padding: 18px;
  font-size: 13px; line-height: 1.65; color: #334155;
}
.help-footer {
  padding: 10px 18px;
  border-top: 1px solid #e2e8f0;
  font-size: 11px; color: #94a3b8; text-align: center;
  background: #f8fafc;
  flex-shrink: 0;
}

/* Slide transition */
.help-slide-enter-active, .help-slide-leave-active {
  transition: opacity .2s ease;
}
.help-slide-enter-active .help-panel,
.help-slide-leave-active .help-panel {
  transition: transform .22s ease;
}
.help-slide-enter-from, .help-slide-leave-to { opacity: 0; }
.help-slide-enter-from .help-panel,
.help-slide-leave-to .help-panel { transform: translateX(100%); }
</style>

<!-- Global styles for v-html content -->
<style>
.help-body h2 { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0 0 12px; }
.help-body h3 { font-size: 13px; font-weight: 700; color: #475569; margin: 14px 0 6px; text-transform: uppercase; letter-spacing: .04em; }
.help-body p  { margin: 0 0 10px; }
.help-body ul { margin: 0 0 10px; padding-left: 18px; }
.help-body li { margin-bottom: 4px; }
.help-body table { width: 100%; border-collapse: collapse; margin: 0 0 10px; font-size: 12px; }
.help-body th { background: #f1f5f9; padding: 5px 8px; text-align: left; font-weight: 600; border: 1px solid #e2e8f0; }
.help-body td { padding: 5px 8px; border: 1px solid #e2e8f0; }
.help-body code { background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-size: 11.5px; font-family: ui-monospace, monospace; color: #6366f1; }
.help-body pre  { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 5px; padding: 8px 10px; overflow-x: auto; font-size: 11px; margin: 0 0 10px; }
.help-body hr   { border: none; border-top: 1px solid #e2e8f0; margin: 12px 0; }
.help-body mark { background: #fef08a; padding: 1px 2px; border-radius: 2px; }
.help-body .help-tip { background: #eff6ff; border-left: 3px solid #3b82f6; padding: 8px 10px; border-radius: 0 5px 5px 0; font-size: 12px; color: #1e40af; margin: 0; }
</style>

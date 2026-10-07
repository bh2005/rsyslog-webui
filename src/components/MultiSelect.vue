<template>
  <div ref="root" class="ms" :class="{ open }">
    <button type="button" class="ms-btn select-inline" :aria-expanded="open" @click="open = !open" @keydown.esc="open = false">
      <span class="ms-label" :class="{ 'ms-placeholder': !modelValue.length }">{{ summary }}</span>
      <span class="ms-caret" aria-hidden="true">▾</span>
    </button>
    <div v-if="open" class="ms-panel" role="listbox" aria-multiselectable="true">
      <label v-for="o in options" :key="o.value" class="ms-opt">
        <input type="checkbox" :checked="modelValue.includes(o.value)" @change="toggle(o.value)" />
        <span>{{ o.label }}</span>
      </label>
      <button v-if="modelValue.length" type="button" class="ms-clear" @click="clear">Auswahl zurücksetzen</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

interface Option { value: string; label: string }

const props = withDefaults(defineProps<{
  modelValue: string[];
  options: Option[];
  placeholder?: string;
}>(), { placeholder: '— alle —' });

const emit = defineEmits<{ (e: 'update:modelValue', v: string[]): void }>();

const open = ref(false);
const root = ref<HTMLElement | null>(null);

const summary = computed(() => {
  const sel = props.modelValue;
  if (!sel.length) return props.placeholder;
  if (sel.length === 1) return props.options.find(o => o.value === sel[0])?.label ?? sel[0];
  return `${sel.length} gewählt`;
});

function toggle(value: string) {
  const sel = props.modelValue.includes(value)
    ? props.modelValue.filter(v => v !== value)
    : [...props.modelValue, value];
  // Reihenfolge der Optionen beibehalten
  emit('update:modelValue', props.options.map(o => o.value).filter(v => sel.includes(v)));
}

function clear() {
  emit('update:modelValue', []);
}

function onDocClick(e: MouseEvent) {
  if (open.value && root.value && !root.value.contains(e.target as Node)) open.value = false;
}

onMounted(() => document.addEventListener('mousedown', onDocClick));
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocClick));
</script>

<style scoped>
.ms { position: relative; min-width: 120px; }
.ms-btn {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  width: 100%; cursor: pointer; text-align: left;
}
.ms-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ms-placeholder { color: var(--text); }
.ms-caret { font-size: 11px; color: var(--text-muted); }
.ms-panel {
  position: absolute; z-index: 20; top: calc(100% + 4px); left: 0;
  min-width: 100%; max-height: 280px; overflow-y: auto;
  background: var(--surface); color: var(--text);
  border: 1px solid var(--border); border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, .18); padding: 4px;
}
.ms-opt {
  display: flex; align-items: center; gap: 8px; padding: 5px 8px;
  border-radius: 5px; font-size: 13px; white-space: nowrap; cursor: pointer;
}
.ms-opt:hover { background: var(--border-soft); }
.ms-opt input { accent-color: var(--ks-400); }
.ms-clear {
  display: block; width: 100%; margin-top: 4px; padding: 6px 8px; border: 0;
  border-top: 1px solid var(--border); background: transparent;
  color: var(--ks-400); font: inherit; font-size: 12px; text-align: left; cursor: pointer;
}
.ms-clear:hover { text-decoration: underline; }
</style>

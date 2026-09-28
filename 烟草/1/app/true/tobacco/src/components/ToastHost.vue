<template>
  <div v-if="message" class="toast" :class="type" role="status" aria-live="polite">
    <component :is="type === 'success' ? CircleCheck : CircleAlert" :size="18" aria-hidden="true" />
    <span>{{ message }}</span>
    <button type="button" aria-label="关闭提示" title="关闭提示" @click="dismiss"><X :size="16" /></button>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { CircleAlert, CircleCheck, X } from '@lucide/vue';

const message = ref('');
const type = ref('error');
let timeout;
function dismiss() { clearTimeout(timeout); message.value = ''; }
function show(event) {
  clearTimeout(timeout);
  message.value = event.detail.message;
  type.value = event.detail.type === 'success' ? 'success' : 'error';
  timeout = setTimeout(dismiss, 4200);
}
onMounted(() => window.addEventListener('app-notify', show));
onUnmounted(() => { window.removeEventListener('app-notify', show); clearTimeout(timeout); });
</script>

<style scoped>
.toast{position:fixed;right:18px;top:74px;z-index:3000;display:flex;align-items:center;gap:10px;width:min(420px,calc(100vw - 32px));padding:12px 13px;border:1px solid #e7d6cf;border-radius:var(--radius-md);background:#fffaf7;color:#85442e;box-shadow:var(--shadow-raised);font-size:13px;line-height:1.5}.toast.success{border-color:#cfe2d5;background:#f5fbf6;color:var(--color-primary)}.toast span{flex:1}.toast button{display:grid;place-items:center;width:24px;height:24px;padding:0;border:0;background:transparent;color:inherit;border-radius:var(--radius-sm)}@media(max-width:600px){.toast{top:12px;right:16px}}
</style>

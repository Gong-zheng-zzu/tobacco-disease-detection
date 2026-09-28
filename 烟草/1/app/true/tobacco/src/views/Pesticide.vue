<template>
  <div class="pesticide-page">
    <header class="page-head">
      <div><span class="eyebrow">植保端</span><h1>农药记录</h1></div>
      <select v-if="parcels.length" v-model="selectedFieldId" aria-label="选择地块">
        <option v-for="parcel in parcels" :key="parcel.id" :value="parcel.id">{{ parcel.name || `${parcel.id}号地块` }}</option>
      </select>
    </header>
    <p v-if="error" class="page-error" role="alert">{{ error }} <button type="button" @click="loadParcels">重试</button></p>
    <p v-else-if="loading" class="page-state">正在加载地块...</p>
    <p v-else-if="!parcels.length" class="page-state">暂无地块，请联系种植端添加地块。</p>
    <section v-else class="records-panel">
      <PesticidePanel :parcel-list="parcels" :selected-field-id="selectedFieldId" />
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import PesticidePanel from '@/components/PesticidePanel.vue';
import { API_BASE } from '@/config/api';

export default {
  name: 'PesticidePage',
  components: { PesticidePanel },
  data: () => ({ parcels: [], selectedFieldId: null, loading: true, error: '' }),
  mounted() { this.loadParcels(); },
  methods: {
    async loadParcels() {
      this.loading = true;
      this.error = '';
      try {
        const uid = localStorage.getItem('userId');
        const response = await axios.get(`${API_BASE}/user/${uid}/fields/list/`);
        this.parcels = response.data.data || [];
        this.selectedFieldId = this.parcels[0]?.id ?? null;
      } catch (error) {
        this.parcels = [];
        this.error = error.response?.data?.msg || '地块加载失败，请检查网络';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.pesticide-page { max-width: 1160px; margin: 0 auto; color: var(--color-text); }
.page-head { display: flex; align-items: end; justify-content: space-between; gap: 16px; padding: 12px 0 18px; }
.eyebrow { color: var(--color-primary); font-size: 12px; font-weight: 600; }
h1 { margin: 4px 0 0; font-size: 24px; font-weight: 600; }
.page-head select { min-width: 180px; max-width: 100%; padding: 9px 12px; border: 1px solid var(--color-border); border-radius: 6px; background: #fff; color: var(--color-text); }
.records-panel { padding: 0; }
.page-error,.page-state { padding: 18px; border: 1px solid var(--color-border); border-radius: 8px; background: #fff; color: var(--color-muted); }
.page-error button { border: 0; padding: 0 4px; background: transparent; color: var(--color-primary); text-decoration: underline; }
@media(max-width:560px) { .page-head { align-items: stretch; flex-direction: column; } .page-head select { width: 100%; } .records-panel { padding: 12px; } }
</style>

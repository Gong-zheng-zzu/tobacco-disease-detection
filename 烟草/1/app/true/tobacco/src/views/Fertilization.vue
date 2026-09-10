<template>
  <div class="fertilization-record">
    <div class="shared-field-row" v-if="parcelList.length > 0">
      <select v-model="selectedFieldId" class="field-select" @change="onFieldSelectChange">
        <option v-for="p in parcelList" :key="p.id" :value="p.id">{{ p.name || p.id + '号地块' }}</option>
      </select>
      <button type="button" class="btn-green btn-green-outline" @click="openCreateFieldDialog">
        新增地块
      </button>
    </div>
    <div class="shared-field-row" v-else>
      <button type="button" class="btn-green btn-green-outline" @click="openCreateFieldDialog">
        新增地块
      </button>
    </div>

    <section class="work-card">
    <div class="card-title-row">
      <div class="card-title">施肥记录</div>
      <button type="button" class="btn-green btn-new-inline" @click="openCreateDialog" :disabled="!getFieldId()">
        新建记录
      </button>
    </div>
    <!-- 选项卡 -->
    <div class="tab-container">
      <button
        class="tab-btn"
        :class="{ 'active': activeTab === 'basic' }"
        @click="activeTab = 'basic'"
      >
        基本施肥记录
      </button>
      <button
        class="tab-btn"
        :class="{ 'active': activeTab === 'topdressing' }"
        @click="activeTab = 'topdressing'"
      >
        追肥记录
      </button>
    </div>

    <div class="record-cards-wrap">
      <div class="record-list-heading">
        {{ listHeadingTitle }}: {{ recordsAfterFilter.length }}
      </div>
      <div class="record-cards-scroll">
        <div v-if="recordsAfterFilter.length === 0" class="record-empty">暂无记录</div>
        <div
          v-for="record in recordsAfterFilter"
          :key="record.id + '-' + (record.ferNum ?? '')"
          class="record-item-card"
        >
        <div class="record-item-main">
          <div class="record-row record-row--muted">
            <span class="lbl">记录编号:</span> {{ record.id }}
          </div>
          <div class="record-row record-row--time">
            <span class="lbl">{{ activeTab === 'basic' ? '施肥时间:' : '追肥时间:' }}</span>
            {{ record.fertilizationTime }}
          </div>
          <div v-if="activeTab === 'basic'" class="record-row record-row--muted">
            <span class="lbl">生长阶段:</span> {{ record.growthStage }}
          </div>
          <div v-else class="record-row record-row--muted">
            <span class="lbl">主要追肥类型:</span> {{ displayMainNutrientType(record) }}
          </div>
          <div class="record-row record-row--fertilizer">
            <span class="lbl">{{ activeTab === 'basic' ? '氮肥消耗量:' : '氮肥追肥量:' }}</span>
            {{ formatKg(record.nitrogen) }}
          </div>
          <div class="record-row record-row--fertilizer">
            <span class="lbl">{{ activeTab === 'basic' ? '磷肥消耗量:' : '磷肥追肥量:' }}</span>
            {{ formatKg(record.phosphorus) }}
          </div>
          <div class="record-row record-row--fertilizer">
            <span class="lbl">{{ activeTab === 'basic' ? '钾肥消耗量:' : '钾肥追肥量:' }}</span>
            {{ formatKg(record.potassium) }}
          </div>
          <div v-if="activeTab === 'basic'" class="record-row record-row--muted record-row--total">
            <span class="lbl">总消耗量:</span> {{ formatKg(record.total) }}
          </div>
        </div>
        <button type="button" class="btn-delete-card" @click="deleteRecord(record)">删除</button>
        </div>
      </div>
    </div>

    <!-- 新建记录弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h3>新建{{ activeTab === 'basic' ? '基本施肥' : '追肥' }}记录</h3>
        <div v-if="activeTab === 'basic'" class="modal-body">
          <label>生长阶段：</label>
          <select v-model="newRecordStage" class="modal-select">
            <option :value="1">苗期</option>
            <option :value="2">还苗期</option>
            <option :value="3">伸根期</option>
            <option :value="4">旺长期</option>
            <option :value="5">成熟期</option>
          </select>
        </div>
        <div v-else class="modal-body">
          <p>追肥记录将根据当前地块缺素情况自动生成，请确认。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showCreateModal = false">取消</button>
          <button class="btn-confirm" @click="submitCreate">确定</button>
        </div>
      </div>
    </div>

    <!-- 新增地块弹窗 -->
    <div v-if="showCreateFieldModal" class="modal-overlay" @click.self="showCreateFieldModal = false">
      <div class="modal-content">
        <h3>新增地块</h3>
        <div class="modal-body modal-form">
          <label for="fieldNameInput">地块名称</label>
          <input id="fieldNameInput" v-model.trim="newFieldForm.name" type="text" class="modal-input" placeholder="例如：3号地块">

          <label for="fieldAreaInput">面积（亩）</label>
          <input
            id="fieldAreaInput"
            v-model.number="newFieldForm.area"
            type="number"
            min="0.01"
            step="0.01"
            class="modal-input"
            placeholder="例如：12.5"
          >

          <label for="fieldTypeInput">肥力类型</label>
          <select id="fieldTypeInput" v-model.number="newFieldForm.field_type" class="modal-select">
            <option :value="1">高肥力</option>
            <option :value="2">中肥力</option>
            <option :value="3">低肥力</option>
          </select>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showCreateFieldModal = false">取消</button>
          <button class="btn-confirm" @click="submitCreateField">确定</button>
        </div>
      </div>
    </div>
    </section>

    <section class="work-card pesticide-wrap">
      <PesticidePanel
        ref="pesticidePanel"
        :parcel-list="parcelList"
        :selected-field-id="selectedFieldId"
      />
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import { API_BASE } from '@/config/api';
import PesticidePanel from '@/components/PesticidePanel.vue';

export default {
  components: { PesticidePanel },
  data() {
    return {
      activeTab: 'basic',
      basicRecords: [],
      topdressingRecords: [],
      isLoading: false,
      showCreateModal: false,
      showCreateFieldModal: false,
      newRecordStage: 1,
      parcelList: [],
      selectedFieldId: null,
      newFieldForm: {
        name: '',
        area: null,
        field_type: 2
      }
    };
  },
  mounted() {
    this.loadParcelList();
  },
  watch: {
    activeTab() {
      this.fetchRecords();
    }
  },
  methods: {
    onFieldSelectChange() {
      this.fetchRecords();
      this.$nextTick(() => this.$refs.pesticidePanel?.refresh?.());
    },
    async loadParcelList() {
      try {
        const uid = localStorage.getItem('userId') || 1;
        const res = await axios.get(`${API_BASE}/user/${uid}/fields/list/`);
        this.parcelList = res.data.data || [];
        if (this.parcelList.length > 0 && !this.selectedFieldId) {
          this.selectedFieldId = this.parcelList[0].id;
        }
        await this.fetchRecords();
      } catch (e) {
        console.error('加载地块列表失败', e);
      }
    },
    getFieldId() {
      return this.selectedFieldId ?? this.parcelList[0]?.id ?? null;
    },
    // 获取基本施肥记录
    async fetchBasicRecords() {
      if (!this.getFieldId()) return;
      this.isLoading = true;
      try {
        const uid = localStorage.getItem('userId') || 1;
        const fieldId = this.getFieldId();
        const response = await axios.get(`${API_BASE}/user/${uid}/fer_records/${fieldId}/`);
        if (response.data.code === 200) {
          this.basicRecords = response.data.data.map(record => ({
            id: record.id,
            ferNum: record.fer_num,
            growthStage: record.growth_stage_display,
            fertilizationTime: record.fer_time,
            nitrogen: record.base_n_used,
            phosphorus: record.base_p_used,
            potassium: record.base_k_used,
            total: record.base_s_used,
            fieldId: record.field_id
          }));
        }
      } catch (error) {
        console.error('获取基本施肥记录失败', error);
      } finally {
        this.isLoading = false;
      }
    },

    // 获取追肥记录
    async fetchTopdressingRecords() {
      if (!this.getFieldId()) return;
      this.isLoading = true;
      try {
        const uid = localStorage.getItem('userId') || 1;
        const fieldId = this.getFieldId();
        const response = await axios.get(`${API_BASE}/user/${uid}/field/${fieldId}/fer_regions/`);
        if (response.data.code === 200) {
          this.topdressingRecords = response.data.data.map(record => ({
            id: record.id,
            combinedNutrientType: record.combined_nutrient_type || '',
            growthStage: '追肥',
            fertilizationTime: record.fer_time,
            nitrogen: record.extra_n_used,
            phosphorus: record.extra_p_used,
            potassium: record.extra_k_used,
            total: parseFloat(record.extra_n_used || 0) + parseFloat(record.extra_p_used || 0) + parseFloat(record.extra_k_used || 0),
            fieldId: record.parcel
          }));
        }
      } catch (error) {
        console.error('获取追肥记录失败', error);
      } finally {
        this.isLoading = false;
      }
    },

    // 初始化加载记录（根据当前activeTab）
    fetchRecords() {
      if (this.activeTab === 'basic') {
        return this.fetchBasicRecords();
      }
      if (this.activeTab === 'topdressing') {
        return this.fetchTopdressingRecords();
      }
      return Promise.resolve();
    },

    openCreateDialog() {
      this.newRecordStage = 1;
      this.showCreateModal = true;
    },
    openCreateFieldDialog() {
      this.newFieldForm = {
        name: '',
        area: null,
        field_type: 2
      };
      this.showCreateFieldModal = true;
    },
    async submitCreateField() {
      const name = (this.newFieldForm.name || '').trim();
      const area = Number(this.newFieldForm.area);
      if (!name) {
        alert('请输入地块名称');
        return;
      }
      if (!Number.isFinite(area) || area <= 0) {
        alert('请输入有效面积');
        return;
      }

      try {
        const uid = localStorage.getItem('userId') || 1;
        const response = await axios.post(`${API_BASE}/user/${uid}/fields/create/`, {
          name,
          area,
          field_type: this.newFieldForm.field_type || 2
        });

        const createdFieldId = response?.data?.data?.id;
        this.showCreateFieldModal = false;
        await this.loadParcelList();
        if (createdFieldId) {
          this.selectedFieldId = createdFieldId;
          await this.onFieldSelectChange();
        }
        alert('地块新增成功');
      } catch (err) {
        console.error('新增地块失败', err);
        alert(err.response?.data?.msg || '新增地块失败，请重试');
      }
    },
    async submitCreate() {
      const fieldId = this.getFieldId();
      if (!fieldId) {
        alert('请先添加地块');
        return;
      }
      this.showCreateModal = false;
      try {
        if (this.activeTab === 'basic') {
          const uid = localStorage.getItem('userId') || 1;
          await axios.post(`${API_BASE}/user/${uid}/fer_records/create/${fieldId}/`, {
            growth_stage: this.newRecordStage
          });
        } else {
          const uid = localStorage.getItem('userId') || 1;
          await axios.post(`${API_BASE}/user/${uid}/field/${fieldId}/fer_regions/`, {});
        }
        await this.fetchRecords();
      } catch (err) {
        console.error('创建失败', err);
        alert(err.response?.data?.msg || '创建失败，请重试');
      }
    },
    async deleteRecord(record) {
      const fieldId = this.getFieldId();
      if (!fieldId) return;
      try {
        const uid = localStorage.getItem('userId') || 1;
        const url = this.activeTab === 'basic'
          ? `${API_BASE}/user/${uid}/fer_records/delete/${fieldId}/${record.ferNum}/`
          : `${API_BASE}/user/${uid}/field/${fieldId}/fer_regions/${record.id}/`;
        await axios.delete(url);
        this.fetchRecords();
      } catch (error) {
        console.error('删除记录失败', error);
        alert('删除记录失败，请重试');
      }
    },
    formatKg(value) {
      const n = parseFloat(value);
      const x = Number.isFinite(n) ? n : 0;
      return `${x.toFixed(2)}Kg`;
    },
    displayMainNutrientType(record) {
      const c = (record.combinedNutrientType || '').trim();
      if (c) return c;
      const n = parseFloat(record.nitrogen) || 0;
      const p = parseFloat(record.phosphorus) || 0;
      const k = parseFloat(record.potassium) || 0;
      const max = Math.max(n, p, k);
      if (max <= 0) return '—';
      if (n >= p && n >= k && n === max) return 'N';
      if (p >= n && p >= k && p === max) return 'P';
      return 'K';
    }
  },
  computed: {
    listHeadingTitle() {
      return this.activeTab === 'basic' ? '基本施肥记录' : '追肥记录';
    },
    recordsAfterFilter() {
      return this.activeTab === 'basic' ? this.basicRecords : this.topdressingRecords;
    }
  }
};
</script>

<style scoped>
.fertilization-record {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.work-card {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 8px 22px rgba(31, 82, 53, 0.08);
  padding: 12px;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.card-title-row .card-title {
  margin-bottom: 0;
  flex-shrink: 0;
}

.btn-new-inline {
  flex-shrink: 0;
  white-space: nowrap;
}

.record-cards-wrap {
  margin: 0 -4px;
  padding: 4px 4px 8px;
  background: #e8eaed;
  border-radius: 10px;
}

.record-cards-scroll {
  max-height: 420px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.record-list-heading {
  font-size: 15px;
  font-weight: 700;
  color: #2e7d4a;
  padding: 10px 8px 8px;
}

.record-empty {
  padding: 24px 12px;
  text-align: center;
  color: #888;
  font-size: 14px;
}

.record-item-card {
  display: flex;
  align-items: stretch;
  gap: 10px;
  background: #fff;
  border-radius: 10px;
  padding: 12px 10px;
  margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.record-item-card:last-child {
  margin-bottom: 2px;
}

.record-item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  line-height: 1.45;
}

.record-row .lbl {
  margin-right: 4px;
}

.record-row--muted {
  color: #333;
}

.record-row--time {
  color: #2e7d4a;
  font-weight: 500;
  word-break: break-all;
}

.record-row--fertilizer {
  color: #c77800;
  font-weight: 500;
}

.record-row--total {
  font-size: 13px;
}

.btn-delete-card {
  align-self: center;
  flex-shrink: 0;
  padding: 8px 14px;
  background: #ef5350;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.btn-delete-card:active {
  opacity: 0.9;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #1f6b44;
  margin-bottom: 10px;
}

.shared-field-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.pesticide-wrap {
  margin-top: 4px;
}

.tab-container {
  margin-bottom: 20px;
}

.tab-btn {
  padding: 8px 16px;
  background: #e8f5e9;
  border: none;
  border-radius: 4px;
  margin-right: 10px;
  cursor: pointer;
  transition: background-color 0.3s;
  color: #2d5a3d;
}

.tab-btn.active {
  background: #66bb6a;
  color: white;
}

.action-area {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.field-select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.btn-green {
  padding: 6px 12px;
  background: #66bb6a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-green:hover:not(:disabled) {
  background: #81c784;
}

.btn-green:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-green-outline {
  background: #fff;
  color: #2f7d50;
  border: 1px solid #66bb6a;
}

.btn-green-outline:hover {
  background: #f4fbf6;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  min-width: 320px;
}

.modal-content h3 { margin: 0 0 16px; color: #2d5a3d; }

.modal-body { margin-bottom: 20px; }

.modal-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  min-width: 120px;
}

.modal-form {
  display: grid;
  gap: 8px;
}

.modal-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 8px 16px;
  background: #e0e0e0;
  color: #333;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-confirm {
  padding: 8px 16px;
  background: #66bb6a;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

@media (orientation: landscape) {
  .fertilization-record {
    padding: 12px;
  }
}
</style>
<template>
  <div class="pesticide-panel">
    <div class="card-title-row">
      <div class="card-title">农药记录</div>
      <button class="btn-green btn-new-inline" type="button" @click="openCreateDialog" :disabled="!getFieldId()">
        新建农药记录
      </button>
    </div>

    <div class="record-cards-wrap">
      <div class="record-list-heading">施药记录: {{ records.length }}</div>
      <div class="record-cards-scroll">
        <div v-if="records.length === 0" class="record-empty">暂无记录</div>
        <div
          v-for="record in records"
          :key="record.id + '-' + record.recordNum"
          class="record-item-card"
        >
          <div class="record-item-main">
            <div class="record-row record-row--muted">
              <span class="lbl">记录编号:</span> {{ record.recordNum }}
            </div>
            <div class="record-row record-row--time">
              <span class="lbl">施药时间:</span> {{ record.sprayTime }}
            </div>
            <div class="record-row record-row--muted">
              <span class="lbl">病害种类:</span> {{ record.targetPest || '—' }}
            </div>
            <div class="record-row record-row--muted">
              <span class="lbl">农药名称:</span> {{ record.pesticideName }}
            </div>
            <div class="record-row record-row--fertilizer">
              <span class="lbl">用量:</span> {{ record.dosageDisplay }}
            </div>
            <div class="record-row record-row--fertilizer">
              <span class="lbl">兑水:</span> {{ waterDisplay }}
            </div>
          </div>
          <button type="button" class="btn-delete-card" @click="deleteRecord(record)">删除</button>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h3>新建农药记录</h3>
        <div class="modal-body">
          <div class="form-row">
            <label>病害种类：</label>
            <select v-model="newRecord.diseaseType" class="modal-select">
              <option value="">请选择病害种类</option>
              <option value="白星病">白星病</option>
              <option value="花叶病">花叶病</option>
              <option value="烟青虫">烟青虫</option>
              <option value="野火病">野火病</option>
            </select>
          </div>
          <div v-if="newRecord.diseaseType" class="form-row preview-row">
            <span class="preview-label">将生成：</span>
            <span class="preview-text">{{ createPreviewText }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn-cancel" @click="showCreateModal = false">取消</button>
          <button type="button" class="btn-confirm" @click="submitCreate" :disabled="!newRecord.diseaseType">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_BASE } from '@/config/api';
import { notify } from '@/utils/notify';

const MU_M2 = 2000 / 3;
const DISEASE_CONFIG = {
  '白星病': { pesticideName: '50% 多菌灵可湿性粉剂', perMu: 100, unit: '克' },
  '花叶病': { pesticideName: '待农技人员确认', unit: '', notes: '请确认病因和当地防治方案后再施药' },
  '烟青虫': { pesticideName: '4.5% 高效氯氰菊酯乳油', perMu: 30, unit: '毫升' },
  '野火病': { pesticideName: '待农技人员确认', unit: '', notes: '请确认病因和当地防治方案后再施药' }
};

export default {
  name: 'PesticidePanel',
  props: {
    parcelList: { type: Array, default: () => [] },
    selectedFieldId: { type: [Number, String], default: null }
  },
  data() {
    return {
      records: [],
      showCreateModal: false,
      newRecord: { diseaseType: '' }
    };
  },
  watch: {
    selectedFieldId() {
      this.fetchRecords();
    },
    parcelList: {
      deep: true,
      handler() {
        this.fetchRecords();
      }
    }
  },
  mounted() {
    this.fetchRecords();
  },
  methods: {
    getFieldId() {
      return this.selectedFieldId ?? this.parcelList[0]?.id ?? null;
    },
    getCurrentFieldArea() {
      const id = this.getFieldId();
      const p = this.parcelList.find(x => x.id === id);
      return p && p.area != null ? Number(p.area) : 0;
    },
    calcDosageByArea(diseaseType) {
      const area = this.getCurrentFieldArea();
      if (!area || !DISEASE_CONFIG[diseaseType]) return 0;
      const config = DISEASE_CONFIG[diseaseType];
      if (!config.perMu) return 0;
      const mu = area / MU_M2;
      return Math.round(mu * config.perMu * 100) / 100;
    },
    async fetchRecords() {
      if (!this.getFieldId()) return;
      try {
        const uid = localStorage.getItem('userId') || 1;
        const fieldId = this.getFieldId();
        const response = await axios.get(`${API_BASE}/user/${uid}/pesticide_records/${fieldId}/`);
        if (response.data.code === 200) {
          this.records = (response.data.data || []).map(record => {
            const dosageDisplay = record.pesticide_name === '待农技人员确认'
              ? '待确认'
              : `${record.dosage} ${record.unit || ''}`.trim();
            return {
              id: record.id,
              recordNum: record.record_num,
              sprayTime: record.spray_time,
              pesticideName: record.pesticide_name,
              dosage: record.dosage,
              unit: record.unit,
              dosageDisplay,
              targetPest: record.target_pest,
              notes: record.notes,
              fieldId: record.field_id
            };
          });
        }
      } catch (error) {
        console.error('获取农药记录失败', error);
      }
    },
    refresh() {
      this.fetchRecords();
    },
    openCreateDialog() {
      this.newRecord = { diseaseType: '' };
      this.showCreateModal = true;
    },
    async submitCreate() {
      const fieldId = this.getFieldId();
      if (!fieldId) {
        notify('请先选择地块');
        return;
      }
      const diseaseType = this.newRecord.diseaseType;
      if (!diseaseType || !DISEASE_CONFIG[diseaseType]) {
        notify('请选择病害种类');
        return;
      }
      const area = this.getCurrentFieldArea();
      if (!area || area <= 0) {
        notify('当前地块面积无效，无法计算用量');
        return;
      }
      const config = DISEASE_CONFIG[diseaseType];
      let pesticideName = config.pesticideName;
      let dosage = 0;
      let unit = config.unit || '';
      let notes = config.notes || '';
      if (config.perMu) {
        dosage = this.calcDosageByArea(diseaseType);
      }
      this.showCreateModal = false;
      try {
        const uid = localStorage.getItem('userId') || 1;
        await axios.post(`${API_BASE}/user/${uid}/pesticide_records/create/${fieldId}/`, {
          pesticide_name: pesticideName,
          dosage,
          unit,
          target_pest: diseaseType,
          notes
        });
        await this.fetchRecords();
      } catch (err) {
        console.error('创建失败', err);
        notify(err.response?.data?.msg || '创建失败，请重试');
      }
    },
    async deleteRecord(record) {
      const fieldId = this.getFieldId();
      if (!fieldId) return;
      try {
        const uid = localStorage.getItem('userId') || 1;
        await axios.delete(
          `${API_BASE}/user/${uid}/pesticide_records/delete/${fieldId}/${record.recordNum}/`
        );
        await this.fetchRecords();
      } catch (error) {
        console.error('删除记录失败', error);
        notify('删除记录失败，请重试');
      }
    }
  },
  computed: {
    waterDisplay() {
      const area = this.getCurrentFieldArea();
      if (!area || area <= 0) return '—';
      const mu = area / MU_M2;
      const kg = Math.round(mu * 40 * 10) / 10;
      return `${kg} 公斤`;
    },
    createPreviewText() {
      const t = this.newRecord.diseaseType;
      if (!t || !DISEASE_CONFIG[t]) return '';
      const config = DISEASE_CONFIG[t];
      const area = this.getCurrentFieldArea();
      if (!area || area <= 0) return `${config.pesticideName}，请先确认地块面积`;
      if (!config.perMu) return `${config.pesticideName}，${config.notes}`;
      const dosage = this.calcDosageByArea(t);
      return `${config.pesticideName}，用量约 ${dosage} ${config.unit}（按当前地块 ${area} m² 折算）`;
    }
  }
};
</script>

<style scoped>
.pesticide-panel {
  margin-top: 0;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #1f6b44;
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

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.modal-content {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  min-width: 360px;
}

.modal-content h3 {
  margin: 0 0 16px;
  color: #2d5a3d;
}

.modal-body {
  margin-bottom: 20px;
}

.form-row {
  margin-bottom: 12px;
}

.form-row label {
  display: inline-block;
  width: 80px;
  color: #333;
}

.modal-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  min-width: 200px;
}

.preview-row {
  margin-top: 8px;
  padding: 10px;
  background: #e8f5e9;
  border-radius: 8px;
}

.preview-label {
  font-weight: 500;
  color: #2d5a3d;
  margin-right: 6px;
}

.preview-text {
  color: #1b5e20;
  font-size: 13px;
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

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.record-cards-wrap{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-sm);overflow:hidden;padding:0;margin:0}
.record-list-heading{padding:10px 16px;background:#fafbfa;border-bottom:1px solid #edf0ed;color:var(--color-muted);font-size:12px;font-weight:500}
.record-item-card,.record-item-card:last-child{min-height:44px;margin:0;padding:12px 16px;border-bottom:1px solid #f0f1f0;border-radius:0;box-shadow:none;transition:background-color .15s}
.record-item-card:last-child{border-bottom:0}
.record-item-card:hover{background:#f9fbf9}
.record-item-main{font-variant-numeric:tabular-nums}
.record-empty{background:#fff;color:var(--color-muted)}
.btn-green,.btn-confirm{background:var(--color-primary)}
.btn-green:hover:not(:disabled),.btn-confirm:hover{background:var(--color-primary-hover)}
</style>

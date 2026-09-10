<template>
  <div class="pesticide-record">
    <!-- 操作和搜索区域 -->
    <div class="action-search-container">
      <div class="action-area">
        <select v-model="selectedFieldId" @change="fetchRecords" class="field-select" v-if="parcelList.length > 0">
          <option v-for="p in parcelList" :key="p.id" :value="p.id">{{ p.name || p.id + '号地块' }}</option>
        </select>
        <button class="btn-green" @click="openCreateDialog" :disabled="!getFieldId()">新建记录</button>
      </div>
      <div class="search-area">
        <div class="search-bar">
          <input
            type="text"
            placeholder="请输入要查找的地块编号"
            v-model="searchField"
          >
          <img src="@/assets/icons/search-icon.png" alt="search-icon" class="search-icon">
        </div>
        <input
          type="text"
          v-model="searchDate"
          class="date-input"
          placeholder="请选择要查找的日期"
          ref="dateInput"
        >
      </div>
    </div>

    <!-- 农药记录表格 -->
    <table class="record-table">
      <thead>
        <tr>
          <th>记录序号</th>
          <th>病害种类</th>
          <th>施药时间</th>
          <th>农药名称</th>
          <th>用量</th>
          <th>兑水</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(record, index) in filteredRecords" :key="index">
          <td>{{ record.recordNum }}</td>
          <td>{{ record.targetPest || '—' }}</td>
          <td>{{ record.sprayTime }}</td>
          <td>{{ record.pesticideName }}</td>
          <td>{{ record.dosageDisplay }}</td>
          <td>{{ waterDisplay }}</td>
          <td><button class="btn-delete" @click="deleteRecord(record)">删除</button></td>
        </tr>
      </tbody>
    </table>

    <!-- 新建记录弹窗：仅选择病害种类，农药名称与用量按地块面积自动计算 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h3>新建农药记录</h3>
        <div class="modal-body">
          <div class="form-row">
            <label>病害种类：</label>
            <select v-model="newRecord.diseaseType" class="modal-select" @change="onDiseaseTypeChange">
              <option value="">请选择病害种类</option>
              <option value="白星病">白星病</option>
              <option value="黄叶病">黄叶病</option>
              <option value="烟青虫">烟青虫</option>
              <option value="叶厚病">叶厚病</option>
            </select>
          </div>
          <div v-if="newRecord.diseaseType" class="form-row preview-row">
            <span class="preview-label">将生成：</span>
            <span class="preview-text">{{ createPreviewText }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showCreateModal = false">取消</button>
          <button class="btn-confirm" @click="submitCreate" :disabled="!newRecord.diseaseType">确定</button>
        </div>
      </div>
    </div>

    <!-- 分页导航 -->
    <div class="pagination">
      <button @click="currentPage = 1">首页</button>
      <button
        :disabled="currentPage <= 1"
        @click="currentPage -= 1"
      >
        上一页
      </button>
      <span>{{ currentPage }}</span>
      <button
        :disabled="currentPage >= totalPages"
        @click="currentPage += 1"
      >
        下一页
      </button>
      <button @click="currentPage = totalPages">尾页</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import flatpickr from 'flatpickr';
import 'flatpickr/dist/flatpickr.min.css';
import 'flatpickr/dist/l10n/zh.js';

// 1 亩 = 2000/3 平方米
const MU_M2 = 2000 / 3;
// 病害种类对应的农药与每亩用量（叶厚病为硼肥 20～30 克 + 磷酸二氢钾 100 克）
const DISEASE_CONFIG = {
  '白星病': { pesticideName: '50% 多菌灵可湿性粉剂', perMu: 100, unit: '克' },
  '黄叶病': { pesticideName: '99% 磷酸二氢钾', perMu: 100, unit: '克' },
  '烟青虫': { pesticideName: '4.5% 高效氯氰菊酯乳油', perMu: 30, unit: '毫升' },
  '叶厚病': {
    pesticideName: '硼肥+磷酸二氢钾',
    unit: '克',
    parts: [
      { name: '硼肥', perMuMin: 20, perMuMax: 30, unit: '克' },
      { name: '磷酸二氢钾', perMu: 100, unit: '克' }
    ]
  }
};

export default {
  data() {
    return {
      searchField: '',
      searchDate: '',
      currentPage: 1,
      pageSize: 10,
      records: [],
      isLoading: false,
      showCreateModal: false,
      parcelList: [],
      selectedFieldId: null,
      newRecord: {
        diseaseType: ''
      }
    };
  },
  mounted() {
    if (this.$refs.dateInput) {
      flatpickr(this.$refs.dateInput, {
        dateFormat: 'Y-m-d',
        placeholder: '请选择要查找的日期',
        locale: 'zh'
      });
    }
    this.loadParcelList();
  },
  methods: {
    async loadParcelList() {
      try {
        const uid = localStorage.getItem('userId') || 1;
        const res = await axios.get(`/api/user/${uid}/fields/list/`);
        this.parcelList = res.data.data || [];
        if (this.parcelList.length > 0 && !this.selectedFieldId) {
          this.selectedFieldId = this.parcelList[0].id;
        }
        this.fetchRecords();
      } catch (e) {
        console.error('加载地块列表失败', e);
      }
    },
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
      if (config.parts) {
        const r = this.calcYehoubingDosage(area);
        return r;
      }
      const mu = area / MU_M2;
      return Math.round(mu * config.perMu * 100) / 100;
    },
    /** 叶厚病：硼肥 20～30 克/亩 + 磷酸二氢钾 100 克/亩，按面积折算后返回展示文案与备注 */
    calcYehoubingDosage(area) {
      const config = DISEASE_CONFIG['叶厚病'];
      if (!config || !config.parts || !area) return { display: '', dosage: 0, notes: '' };
      const mu = area / MU_M2;
      const [boron, phosph] = config.parts;
      const bMin = Math.round(mu * boron.perMuMin * 10) / 10;
      const bMax = Math.round(mu * boron.perMuMax * 10) / 10;
      const pVal = Math.round(mu * phosph.perMu * 10) / 10;
      const display = `${boron.name} ${bMin}～${bMax} ${boron.unit}+${phosph.name} ${pVal} ${phosph.unit}`;
      const notes = `${bMin}～${bMax} ${boron.unit}+${pVal} ${phosph.unit}`;
      return { display, dosage: pVal, notes };
    },
    onDiseaseTypeChange() {
      // 仅选择病害，预览由 createPreviewText 计算属性展示
    },
    async fetchRecords() {
      if (!this.getFieldId()) return;
      this.isLoading = true;
      try {
        const uid = localStorage.getItem('userId') || 1;
        const fieldId = this.getFieldId();
        const response = await axios.get(`/api/user/${uid}/pesticide_records/${fieldId}/`);
        if (response.data.code === 200) {
          this.records = (response.data.data || []).map(record => {
            const isYehoubing = record.target_pest === '叶厚病';
            const dosageDisplay = isYehoubing && record.notes
              ? record.notes
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
      } finally {
        this.isLoading = false;
      }
    },
    openCreateDialog() {
      this.newRecord = { diseaseType: '' };
      this.showCreateModal = true;
    },
    async submitCreate() {
      const fieldId = this.getFieldId();
      if (!fieldId) {
        alert('请先选择地块');
        return;
      }
      const diseaseType = this.newRecord.diseaseType;
      if (!diseaseType || !DISEASE_CONFIG[diseaseType]) {
        alert('请选择病害种类');
        return;
      }
      const area = this.getCurrentFieldArea();
      if (!area || area <= 0) {
        alert('当前地块面积无效，无法计算用量');
        return;
      }
      const config = DISEASE_CONFIG[diseaseType];
      let pesticideName = config.pesticideName;
      let dosage = 0;
      let unit = config.unit || '克';
      let notes = '';
      if (config.parts) {
        const r = this.calcYehoubingDosage(area);
        dosage = r.dosage;
        notes = r.notes;
      } else {
        dosage = this.calcDosageByArea(diseaseType);
      }
      this.showCreateModal = false;
      try {
        const uid = localStorage.getItem('userId') || 1;
        await axios.post(`/api/user/${uid}/pesticide_records/create/${fieldId}/`, {
          pesticide_name: pesticideName,
          dosage,
          unit,
          target_pest: diseaseType,
          notes
        });
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
        await axios.delete(
          `/api/user/${uid}/pesticide_records/delete/${fieldId}/${record.recordNum}/`
        );
        this.fetchRecords();
      } catch (error) {
        console.error('删除记录失败', error);
        alert('删除记录失败，请重试');
      }
    }
  },
  computed: {
    /** 兑水：每亩 40 公斤，按当前地块面积折算 */
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
      if (config.parts) {
        const r = this.calcYehoubingDosage(area);
        return `${config.pesticideName}，用量：${r.display}（按当前地块 ${area} m² 折算）`;
      }
      const dosage = this.calcDosageByArea(t);
      return `${config.pesticideName}，用量约 ${dosage} ${config.unit}（按当前地块 ${area} m² 折算）`;
    },
    filteredRecords() {
      let filtered = this.records.filter(record => {
        if (this.searchField && record.fieldId != null && !String(record.fieldId).includes(this.searchField)) {
          return false;
        }
        if (this.searchDate && record.sprayTime) {
          const recordDate = String(record.sprayTime)
            .replace(/年/g, '-')
            .replace(/月/g, '-')
            .replace(/日/g, '')
            .split(' ')[0];
          if (recordDate !== this.searchDate) return false;
        }
        return true;
      });
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return filtered.slice(start, end);
    },
    totalPages() {
      const filtered = this.records.filter(record => {
        if (this.searchField && record.fieldId != null && !String(record.fieldId).includes(this.searchField)) return false;
        if (this.searchDate && record.sprayTime) {
          const recordDate = String(record.sprayTime)
            .replace(/年/g, '-').replace(/月/g, '-').replace(/日/g, '').split(' ')[0];
          if (recordDate !== this.searchDate) return false;
        }
        return true;
      });
      const total = filtered.length;
      return Math.max(1, Math.ceil(total / this.pageSize));
    }
  }
};
</script>

<style scoped>
.pesticide-record {
  padding: 20px;
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

.action-search-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.search-area {
  display: flex;
  gap: 15px;
}

.search-bar {
  display: none; /* 地块编号搜索框隐藏，仅保留日期 */
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0 8px;
  width: 300px;
}

.search-bar input {
  border: none;
  outline: none;
  padding: 6px;
  width: 100%;
}

.search-icon {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.date-input {
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: auto;
}

.record-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.record-table th,
.record-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.record-table th {
  background-color: #f2f2f2;
}

.btn-delete {
  padding: 4px 8px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
}

.pagination button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  background: white;
  transition: border-color 0.3s, background-color 0.3s;
}

.pagination button:disabled {
  color: #999;
  cursor: not-allowed;
  border-color: #ddd;
  background: #f2f2f2;
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

.modal-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  min-width: 200px;
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

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
</style>

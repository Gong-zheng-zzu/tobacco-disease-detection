<template>
  <div class="fertilization-record">
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

    <!-- 操作和搜索区域（合并到同一行） -->
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

    <!-- 施肥记录表格 -->
    <table class="record-table">
      <thead>
        <tr>
          <th>记录序号</th>
          <th>生长阶段</th>
          <th>施肥时间</th>
          <th>氮肥消耗量</th>
          <th>磷肥消耗量</th>
          <th>钾肥消耗量</th>
          <th>总消耗量</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(record, index) in filteredRecords" :key="index">
          <td>{{ record.id }}</td>
          <td>{{ record.growthStage }}</td>
          <td>{{ record.fertilizationTime }}</td>
          <td>{{ record.nitrogen }}</td>
          <td>{{ record.phosphorus }}</td>
          <td>{{ record.potassium }}</td>
          <td>{{ record.total }}</td>
          <td><button class="btn-delete" @click="deleteRecord(record)">删除</button></td>
        </tr>
      </tbody>
    </table>

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
import 'flatpickr/dist/l10n/zh.js'; // 引入中文语言包

export default {
  data() {
    return {
      activeTab: 'basic',
      searchField: '',
      searchDate: '',
      currentPage: 1,
      pageSize: 10,
      basicRecords: [],
      topdressingRecords: [],
      isLoading: false,
      showCreateModal: false,
      newRecordStage: 1,
      parcelList: [],
      selectedFieldId: null
    };
  },
  mounted() {
    flatpickr(this.$refs.dateInput, {
      dateFormat: 'Y-m-d', 
      placeholder: '请选择要查找的日期',
      locale: 'zh'
    });
    this.loadParcelList();
  },
  watch: {
    activeTab(newVal) {
      this.currentPage = 1; // 切换选项卡时重置页码
      this.fetchRecords();
    }
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
    // 获取基本施肥记录
    async fetchBasicRecords() {
      if (!this.getFieldId()) return;
      this.isLoading = true;
      try {
        const uid = localStorage.getItem('userId') || 1;
        const fieldId = this.getFieldId();
        const response = await axios.get(`/api/user/${uid}/fer_records/${fieldId}/`);
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
        const response = await axios.get(`/api/user/${uid}/field/${fieldId}/fer_regions/`);
        if (response.data.code === 200) {
          this.topdressingRecords = response.data.data.map(record => ({
            id: record.id,
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
          await axios.post(`/api/user/${uid}/fer_records/create/${fieldId}/`, {
            growth_stage: this.newRecordStage
          });
        } else {
          const uid = localStorage.getItem('userId') || 1;
          await axios.post(`/api/user/${uid}/field/${fieldId}/fer_regions/`, {});
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
          ? `/api/user/${uid}/fer_records/delete/${fieldId}/${record.ferNum}/`
          : `/api/user/${uid}/field/${fieldId}/fer_regions/${record.id}/`;
        await axios.delete(url);
        this.fetchRecords();
      } catch (error) {
        console.error('删除记录失败', error);
        alert('删除记录失败，请重试');
      }
    }
  },
  computed: {
    // 合并并过滤记录
    filteredRecords() {
      const currentRecords = this.activeTab === 'basic' ? this.basicRecords : this.topdressingRecords;
      
      let filtered = currentRecords.filter(record => {
        if (this.searchField && record.fieldId != null && !String(record.fieldId).includes(this.searchField)) {
          return false;
        }
        if (this.searchDate && record.fertilizationTime) {
          const recordDate = String(record.fertilizationTime)
            .replace(/年/g, '-')
            .replace(/月/g, '-')
            .replace(/日/g, '')
            .split(' ')[0];
          if (recordDate !== this.searchDate) return false;
        }
        return true;
      });

      // 分页处理
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return filtered.slice(start, end);
    },

    totalPages() {
      const totalRecords = this.activeTab === 'basic' ? this.basicRecords.length : this.topdressingRecords.length;
      return Math.ceil(totalRecords / this.pageSize);
    }
  }
};
</script>

<style scoped>
.fertilization-record {
  padding: 20px;
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

.pagination button:disabled {
  color: #999;
  cursor: not-allowed;
  border-color: #ddd;
  background: #f2f2f2;
}
</style>
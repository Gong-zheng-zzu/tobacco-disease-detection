<template>
  <div class="device-management-page">
    <!-- 左侧地块传感器区域 -->
    <div class="left-section">
      <div class="top-bar">
        <div class="filter-buttons">
          <button class="button" :class="{ active: viewMode === 'all' }" @click="viewMode = 'all'; selectedFieldId = null">全部地块</button>
          <button class="button" :class="{ active: viewMode === 'single' }" @click="viewMode = 'single'">单个地块</button>
        </div>
        <div class="search-bar">
          <input v-model="searchKeyword" type="text" placeholder="搜索设备名称或ID">
          <img :src="searchIcon" alt="search-icon" class="search-icon">
        </div>
      </div>
      <div v-if="viewMode === 'single'" class="field-select-area">
        <select v-model="selectedFieldId" class="field-select-dropdown">
          <option :value="null" disabled>请选择地块</option>
          <option v-for="f in fieldList" :key="f.id" :value="f.id">{{ f.name || (f.id + '号地块') }}（{{ f.area }} m²）</option>
        </select>
      </div>
      <div class="current-field-hint">当前查看：{{ viewMode === 'all' ? '全部地块' : (selectedFieldName || '请选择地块') }}</div>
      <h2 class="overview-title">设备概况</h2>
      <div class="sensor-container">
        <div class="sensor-item">
          <div class="sensor-info">
            <div class="sensor-title">在线设备</div>
            <div class="sensor-value">{{ onlineDeviceCount }} <span class="unit">台</span></div>
          </div>
        </div>
        <div class="sensor-item">
          <div class="sensor-info">
            <div class="sensor-title">离线设备</div>
            <div class="sensor-value">{{ offlineDeviceCount }} <span class="unit">台</span></div>
          </div>
        </div>
        <div class="sensor-item">
          <div class="sensor-info">
            <div class="sensor-title">关联地块</div>
            <div class="sensor-value">{{ linkedFieldCount }} <span class="unit">块</span></div>
          </div>
        </div>
      </div>
    </div>
    <!-- 右侧设备状态区域 -->
    <div class="right-section">
      <div class="alarm-info">
        <div><h2>设备档案</h2><p>设备状态来自档案；环境数据尚未接入自动采集。</p></div>
        <button class="btn-add" @click="openAddModal">+ 新建设备</button>
      </div>
      <div class="device-list">
        <p v-if="deviceError" class="device-feedback">{{ deviceError }} <button type="button" @click="fetchDevices">重试</button></p>
        <p v-else-if="!filteredDevices.length" class="device-feedback">暂无符合条件的设备</p>
        <div
          v-for="device in filteredDevices"
          :key="device.id"
          class="device-item"
          :class="{ 'offline': device.status === '离线' }"
        >
          <img
            :src="getDeviceIcon(device.type)"
            :alt="`${device.type}-icon`"
            class="device-icon"
          >
          <div class="device-details">
            <div class="device-name">{{ device.name }}</div>
            <div class="device-meta"><span>编号 {{ device.id }}</span><span>{{ device.type }}</span><span>{{ getFieldName(device.field_id) }}</span></div>
          </div>
          <div class="device-actions">
            <button class="button green" @click="editDevice(device)">修改</button>
            <button class="button red" @click="deleteDevice(device)">删除</button>
          </div>
          <div class="device-status">
            <span :class="device.status === '在线' ? 'status-online' : 'status-offline'">{{ device.status }}</span>
            <button type="button"
              class="switch"
              :class="{ 'on': device.status === '在线', 'off': device.status === '离线' }"
              role="switch"
              :aria-label="`切换 ${device.name} 状态`"
              :aria-checked="device.status === '在线'"
              @click="toggleStatus(device)"
            ></button>
          </div>
        </div>
      </div>
    </div>

    <!-- 修改设备弹窗 -->
    <div v-if="editModalVisible" class="modal-overlay" @click.self="editModalVisible = false">
      <div class="modal-content">
        <h3>修改设备</h3>
        <div class="modal-body">
          <div class="form-row">
            <label>设备名称：</label>
            <input v-model="editForm.name" type="text" class="modal-input">
          </div>
          <div class="form-row">
            <label>设备类型：</label>
            <select v-model="editForm.type" class="modal-select">
              <option value="无人机">无人机</option>
              <option value="传感器">传感器</option>
              <option value="执行器">执行器</option>
            </select>
          </div>
          <div class="form-row">
            <label>所属地块：</label>
            <select v-model="editForm.field_id" class="modal-select">
              <option :value="null">未分配</option>
              <option v-for="f in fieldList" :key="f.id" :value="f.id">{{ f.name || (f.id + '号地块') }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="editModalVisible = false">取消</button>
          <button class="btn-confirm" @click="saveEdit">保存</button>
        </div>
      </div>
    </div>

    <!-- 新建设备弹窗 -->
    <div v-if="addModalVisible" class="modal-overlay" @click.self="addModalVisible = false">
      <div class="modal-content">
        <h3>新建设备</h3>
        <div class="modal-body">
          <div class="form-row">
            <label>设备名称：</label>
            <input v-model="addForm.name" type="text" class="modal-input" placeholder="请输入设备名称">
          </div>
          <div class="form-row">
            <label>设备类型：</label>
            <select v-model="addForm.type" class="modal-select">
              <option value="无人机">无人机</option>
              <option value="传感器">传感器</option>
              <option value="执行器">执行器</option>
            </select>
          </div>
          <div class="form-row">
            <label>所属地块：</label>
            <select v-model="addForm.field_id" class="modal-select">
              <option :value="null">未分配</option>
              <option v-for="f in fieldList" :key="f.id" :value="f.id">{{ f.name || (f.id + '号地块') }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="addModalVisible = false">取消</button>
          <button class="btn-confirm" @click="submitAdd">确定</button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="deleteModalVisible" class="modal-overlay" @click.self="deleteModalVisible = false">
      <div class="modal-content">
        <h3>确认删除</h3>
        <div class="modal-body">
          <p class="delete-confirm-text">确定要删除设备「{{ deviceToDelete?.name }}」吗？</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="deleteModalVisible = false">取消</button>
          <button class="btn-confirm btn-delete" @click="confirmDelete">确定删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import searchIcon from '@/assets/icons/search-icon.png';
import soilMoistureIcon from '@/assets/icons/sensor_icon/soil-moisture-icon.png';
import temperatureIcon from '@/assets/icons/sensor_icon/air_temperature-icon.png';
import humidityIcon from '@/assets/icons/sensor_icon/humidity-icon.png';
import droneIcon from '@/assets/icons/sensor_icon/drone-icon.png';
import sensorIcon from '@/assets/icons/sensor_icon/sensor-icon.png';
import actuatorIcon from '@/assets/icons/sensor_icon/actuator-icon.png';
import { API_BASE } from '@/config/api';
import { notify } from '@/utils/notify';

export default {
  data() {
    return {
      searchIcon,
      soilMoistureIcon,
      temperatureIcon,
      humidityIcon,
      droneIcon,
      sensorIcon,
      actuatorIcon,
      viewMode: 'all',
      fieldList: [],
      selectedFieldId: null,
      editModalVisible: false,
      editForm: { id: null, name: '', type: '', field_id: null },
      addModalVisible: false,
      addForm: { name: '', type: '传感器', field_id: null },
      deleteModalVisible: false,
      deviceToDelete: null,
      devices: [],
      searchKeyword: '',
      userId: parseInt(localStorage.getItem('userId') || '1', 10),
      apiBase: API_BASE,
      deviceError: ''
    };
  },
  watch: {
    viewMode() {
      this.fetchDevices();
    },
    selectedFieldId() {
      this.fetchDevices();
    }
  },
  methods: {
    async loadFieldList() {
      try {
        const res = await axios.get(`${this.apiBase}/user/${this.userId}/fields/list/`);
        if (res.data?.code === 200) this.fieldList = res.data.data || [];
      } catch (e) {
        this.fieldList = [];
      }
    },
    async fetchDevices() {
      this.deviceError = '';
      try {
        let url = `${this.apiBase}/user/${this.userId}/devices/`;
        if (this.viewMode === 'single' && this.selectedFieldId) {
          url += `?field_id=${this.selectedFieldId}`;
        }
        const res = await axios.get(url);
        if (res.data.code === 200) this.devices = res.data.data || [];
      } catch (e) {
        console.error('获取设备失败', e);
        this.devices = [];
        this.deviceError = '设备列表加载失败';
      }
    },
    getFieldName(fieldId) {
      if (fieldId == null) return '未分配';
      const f = this.fieldList.find(x => x.id === fieldId);
      return f ? (f.name || f.id + '号地块') : '未知地块';
    },
    editDevice(device) {
      this.editForm = { id: device.id, name: device.name, type: device.type, field_id: device.field_id ?? null };
      this.editModalVisible = true;
    },
    async saveEdit() {
      try {
        await axios.put(`${this.apiBase}/user/${this.userId}/devices/${this.editForm.id}/`, {
          name: this.editForm.name,
          type: this.editForm.type,
          field_id: this.editForm.field_id
        });
        this.editModalVisible = false;
        this.fetchDevices();
      } catch (e) {
        notify(e.response?.data?.msg || '修改失败');
      }
    },
    async toggleStatus(device) {
      const newStatus = device.status === '在线' ? '离线' : '在线';
      try {
        await axios.put(`${this.apiBase}/user/${this.userId}/devices/${device.id}/`, { status: newStatus });
        device.status = newStatus;
      } catch (e) {
        notify(e.response?.data?.msg || '状态切换失败');
      }
    },
    deleteDevice(device) {
      this.deviceToDelete = device;
      this.deleteModalVisible = true;
    },
    async confirmDelete() {
      if (!this.deviceToDelete) return;
      try {
        await axios.delete(`${this.apiBase}/user/${this.userId}/devices/${this.deviceToDelete.id}/`);
        this.deleteModalVisible = false;
        this.deviceToDelete = null;
        this.fetchDevices();
      } catch (e) {
        notify(e.response?.data?.msg || '删除失败');
      }
    },
    openAddModal() {
      this.addForm = { name: '', type: '传感器', field_id: this.viewMode === 'single' && this.selectedFieldId ? this.selectedFieldId : null };
      this.addModalVisible = true;
    },
    async submitAdd() {
      if (!this.addForm.name.trim()) {
        notify('请输入设备名称');
        return;
      }
      const payload = { name: this.addForm.name.trim(), type: this.addForm.type };
      if (this.addForm.field_id != null) payload.field_id = this.addForm.field_id;
      try {
        await axios.post(`${this.apiBase}/user/${this.userId}/devices/`, payload);
        this.addModalVisible = false;
        this.fetchDevices();
      } catch (e) {
        notify(e.response?.data?.msg || e.response?.data?.errors || '创建失败');
      }
    },
    getDeviceIcon(type) {
      const iconMap = {
        无人机: this.droneIcon,
        传感器: this.sensorIcon,
        执行器: this.actuatorIcon
      };
      return iconMap[type] || this.sensorIcon; // Fallback to sensor icon
    }
  },
  computed: {
    selectedFieldName() {
      if (!this.selectedFieldId) return '';
      const f = this.fieldList.find(x => x.id === this.selectedFieldId);
      return f ? (f.name || f.id + '号地块') : '';
    },
    filteredDevices() {
      const kw = (this.searchKeyword || '').trim().toLowerCase();
      if (!kw) return this.devices;
      return this.devices.filter(
        (d) =>
          String(d.name || '').toLowerCase().includes(kw) ||
          String(d.id || '').includes(kw) ||
          String(d.type || '').toLowerCase().includes(kw)
      );
    },
    onlineDeviceCount() { return this.devices.filter(device => device.status === '在线').length; },
    offlineDeviceCount() { return this.devices.filter(device => device.status === '离线').length; },
    linkedFieldCount() { return new Set(this.devices.map(device => device.field_id).filter(Boolean)).size; }
  },
  mounted() {
    this.loadFieldList().then(() => this.fetchDevices());
  }
};
</script>

<style scoped>
.device-management-page {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  padding: 10px;
  height: auto;
  box-sizing: border-box;
  overflow: visible;
}

.left-section,
.right-section {
  padding: 18px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  min-height: 0;
  border: 1px solid #e3e9e4;
  box-shadow: 0 1px 2px rgba(16, 24, 40, .04);
}

.right-section { overflow: visible; }

.left-section {
  background: #fff;
  color: #263b30;
  height: auto;
  align-self: start;
}

.right-section {
  background: #ffffff;
}

.top-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 0;
}

.search-bar { display: flex; flex: 1; min-width: 180px; position: relative; }

.search-bar input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 16px;
}

.search-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  cursor: pointer;
}

.filter-buttons {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.field-select-area {
  margin-bottom: 0;
}

.field-select-dropdown {
  width: 100%;
  height: 40px;
  border-radius: 10px;
  border: 1px solid #d8e2da;
  padding: 0 12px;
  font-size: 14px;
  background-color: rgba(255, 255, 255, 0.9);
  color: #333;
}

.current-field-hint {
  margin-bottom: 0;
  font-size: 13px;
  padding: 8px 10px;
  background-color: #f5f7f5;
  border-radius: 10px;
}

.button {
  padding: 8px 14px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  background-color: #ffffff;
  color: #1f6f4a;
  border: 1px solid #d8e2da;
  font-weight: 700;
  transition: background-color 0.3s;
}

.button:hover {
  background-color: #eef4ef;
}

.button.active {
  background-color: #e8f1eb;
  border: 1px solid #0d8f5e;
}

.sensor-container {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.overview-title { margin: 4px 0 0; font-size: 15px; color: #244334; font-weight: 600; }

.sensor-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: #f8faf8;
  color: #2f5644;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #d9efdf;
}

.sensor-icon {
  width: 30px;
  height: 30px;
}

.sensor-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.sensor-title {
  font-size: 13px;
  font-weight: 700;
  color: #2b6a49;
}

.sensor-value {
  font-size: 25px;
  font-weight: 700;
}

.unit {
  font-size: 12px;
  color: #6f897d;
  font-weight: normal;
}

.alarm-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #e8eee9;
}
.alarm-info h2 { margin: 0 0 4px; color: #244334; font-size: 16px; font-weight: 600; }
.alarm-info p { margin: 0; color: #6b7d70; font-size: 13px; line-height: 1.5; }

.btn-add {
  padding: 9px 14px;
  background: #1f6f4a;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  flex-shrink: 0;
}

.btn-add:hover {
  background: #185c3e;
}

.device-list {
  min-height: 120px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr));
  align-items: stretch;
  gap: 12px;
}

.device-item {
  background-color: #fff;
  padding: 16px;
  border-radius: 8px;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  grid-template-areas:
    "icon detail status"
    "actions actions actions";
  align-content: space-between;
  gap: 12px;
  border: 1px solid #ddefe3;
  border-left: 3px solid #1f6f4a;
  min-height: 148px;
}

.device-item.offline {
  border-left-color: #ef5e5e;
}

.device-icon {
  grid-area: icon;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  object-fit: contain;
}

.device-details {
  grid-area: detail;
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}

.device-name {
  font-size: 15px;
  font-weight: 600;
  overflow-wrap: anywhere;
}
.device-meta { display: flex; flex-wrap: wrap; gap: 4px 10px; color: #6f8a7d; font-size: 12px; line-height: 1.4; }

.device-actions {
  grid-area: actions;
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid #eef1ee;
}
.device-actions .button { min-width: 60px; min-height: 38px; box-sizing: border-box; }

.green {
  background-color: #1f6f4a;
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.green:hover {
  background-color: #289c60;
}

.red {
  background-color: #fff;
  border: 1px solid #e7cccc;
  color: #a44848;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.red:hover {
  background-color: #fdf4f4;
}

.device-status {
  grid-area: status;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #587a6b;
  justify-content: flex-end;
  align-self: start;
  white-space: nowrap;
}
.status-online { color: #1f6f4a; }
.status-offline { color: #8c5555; }

.switch {
  width: 34px;
  height: 18px;
  border-radius: 15px;
  cursor: pointer;
  position: relative;
  border: 1px solid #acc5b8;
  flex: 0 0 34px;
  padding: 0;
}

.switch::before {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  background-color: #fff;
  border-radius: 50%;
  top: 1px;
  transition: transform 0.2s;
}

.on {
  background-color: #30b372;
}

.on::before {
  transform: translateX(16px);
}

.off {
  background-color: #d3dcda;
}

.off::before {
  transform: translateX(1px);
}

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  padding: 18px;
  border-radius: 14px;
  width: min(92vw, 420px);
}

.modal-content h3 {
  margin: 0 0 14px;
  color: #246948;
}

.modal-body { margin-bottom: 20px; }

.form-row {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-row label {
  min-width: 74px;
  font-size: 13px;
}

.modal-input, .modal-select {
  flex: 1;
  padding: 9px 10px;
  border: 1px solid #d5e5de;
  border-radius: 8px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 8px 16px;
  background: #f1f4f5;
  color: #49555c;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-confirm {
  padding: 8px 16px;
  background: #1f6f4a;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-delete {
  background: #ef5e5e;
}

.btn-delete:hover {
  background: #da4d4d;
}

.delete-confirm-text {
  margin: 0;
  font-size: 14px;
  color: #2f4440;
}

.device-feedback { margin: 0; padding: 24px 10px; color: #6b7d70; text-align: center; font-size: 14px; }
.device-feedback button { margin-left: 8px; color: #1f6f4a; background: transparent; border: 0; text-decoration: underline; }

@media (max-width: 640px) {
  .sensor-container { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .sensor-item { padding: 10px; }
  .sensor-value { font-size: 21px; }
  .alarm-info { align-items: flex-start; flex-direction: column; }
}
</style>

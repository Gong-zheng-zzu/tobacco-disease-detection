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
      <div class="sensor-container">
        <div class="sensor-item">
          <img :src="soilMoistureIcon" alt="soil-moisture-icon" class="sensor-icon">
          <div class="sensor-info">
            <div class="sensor-title">土壤湿度</div>
            <div class="sensor-value">
              {{ soilMoistureDisplay }}
              <span class="unit">VWC</span>
            </div>
          </div>
        </div>
        <div class="sensor-item">
          <img :src="temperatureIcon" alt="temperature-icon" class="sensor-icon">
          <div class="sensor-info">
            <div class="sensor-title">空气温度</div>
            <div class="sensor-value">{{ airTemperatureDisplay }}</div>
          </div>
        </div>
        <div class="sensor-item">
          <img :src="humidityIcon" alt="humidity-icon" class="sensor-icon">
          <div class="sensor-info">
            <div class="sensor-title">空气湿度</div>
            <div class="sensor-value">
              {{ airHumidityDisplay }}
              <span class="unit">RH</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 右侧设备状态区域 -->
    <div class="right-section">
      <div class="alarm-info">
        <button class="btn-add" @click="openAddModal">+ 新建设备</button>
        <span>报警信息: 传感器传输数据正常</span>
      </div>
      <div class="device-list">
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
            <div class="device-id">ID:{{ device.id }} {{ device.status }}</div>
            <div class="device-name">{{ device.name }}</div>
            <div class="device-type">类型: {{ device.type }}</div>
            <div class="device-field">所属: {{ getFieldName(device.field_id) }}</div>
          </div>
          <div class="device-actions">
            <button class="button green" @click="editDevice(device)">修改</button>
            <button class="button red" @click="deleteDevice(device)">删除</button>
          </div>
          <div class="device-status">
            <span>状态:</span>
            <span
              class="switch"
              :class="{ 'on': device.status === '在线', 'off': device.status === '离线' }"
              @click="toggleStatus(device)"
            ></span>
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
      // 传感器展示数值
      sensorValues: {
        soilMoisture: '24%–28%',
        airTemperature: '25–28°C',
        airHumidity: '65%–75%'
      }
    };
  },
  watch: {
    viewMode() {
      this.fetchDevices();
      this.updateSensorValues();
    },
    selectedFieldId() {
      this.fetchDevices();
      this.updateSensorValues();
    }
  },
  methods: {
    updateSensorValues() {
      // 仅在“单个地块”且已选择地块时随机显示区间内具体值
      if (this.viewMode === 'single' && this.selectedFieldId) {
        const randInRange = (min, max, decimals = 1) => {
          const v = Math.random() * (max - min) + min;
          return v.toFixed(decimals);
        };
        this.sensorValues.soilMoisture = `${randInRange(24, 28)}%`;
        this.sensorValues.airTemperature = `${randInRange(25, 28, 1)}°C`;
        this.sensorValues.airHumidity = `${randInRange(65, 75)}%`;
      } else {
        // 查看全部地块时，显示区间
        this.sensorValues.soilMoisture = '24%–28%';
        this.sensorValues.airTemperature = '25–28°C';
        this.sensorValues.airHumidity = '65%–75%';
      }
    },
    async loadFieldList() {
      try {
        const res = await axios.get(`${this.apiBase}/user/${this.userId}/fields/list/`);
        if (res.data?.code === 200) this.fieldList = res.data.data || [];
      } catch (e) {
        this.fieldList = [];
      }
    },
    async fetchDevices() {
      try {
        let url = `${this.apiBase}/user/${this.userId}/devices/`;
        if (this.viewMode === 'single' && this.selectedFieldId) {
          url += `?field_id=${this.selectedFieldId}`;
        }
        const res = await axios.get(url);
        if (res.data.code === 200) this.devices = res.data.data || [];
      } catch (e) {
        console.error('获取设备失败', e);
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
        alert(e.response?.data?.msg || '修改失败');
      }
    },
    async toggleStatus(device) {
      const newStatus = device.status === '在线' ? '离线' : '在线';
      try {
        await axios.put(`${this.apiBase}/user/${this.userId}/devices/${device.id}/`, { status: newStatus });
        device.status = newStatus;
      } catch (e) {
        alert(e.response?.data?.msg || '状态切换失败');
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
        alert(e.response?.data?.msg || '删除失败');
      }
    },
    openAddModal() {
      this.addForm = { name: '', type: '传感器', field_id: this.viewMode === 'single' && this.selectedFieldId ? this.selectedFieldId : null };
      this.addModalVisible = true;
    },
    async submitAdd() {
      if (!this.addForm.name.trim()) {
        alert('请输入设备名称');
        return;
      }
      const payload = { name: this.addForm.name.trim(), type: this.addForm.type };
      if (this.addForm.field_id != null) payload.field_id = this.addForm.field_id;
      try {
        await axios.post(`${this.apiBase}/user/${this.userId}/devices/`, payload);
        this.addModalVisible = false;
        this.fetchDevices();
      } catch (e) {
        alert(e.response?.data?.msg || e.response?.data?.errors || '创建失败');
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
    soilMoistureDisplay() {
      return this.sensorValues.soilMoisture;
    },
    airTemperatureDisplay() {
      return this.sensorValues.airTemperature;
    },
    airHumidityDisplay() {
      return this.sensorValues.airHumidity;
    }
  },
  mounted() {
    this.loadFieldList().then(() => this.fetchDevices());
    this.updateSensorValues();
  }
};
</script>

<style scoped>
.device-management-page {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  padding: 6px;
  height: auto;
  box-sizing: border-box;
  overflow: visible;
}

.left-section,
.right-section {
  padding: 12px;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  min-height: 0;
  box-shadow: 0 8px 22px rgba(35, 93, 61, 0.08);
}

.left-section {
  background: linear-gradient(150deg, #147e55, #26ac71);
  color: #fff;
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

.search-bar {
  display: none; /* 隐藏，保留逻辑 */
}

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
  border: 1px solid rgba(255, 255, 255, 0.5);
  padding: 0 12px;
  font-size: 14px;
  background-color: rgba(255, 255, 255, 0.9);
  color: #333;
}

.current-field-hint {
  margin-bottom: 0;
  font-size: 13px;
  padding: 8px 10px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
}

.button {
  padding: 8px 14px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  background-color: #ffffff;
  color: #008b8b;
  font-weight: 700;
  transition: background-color 0.3s;
}

.button:hover {
  background-color: #e0f7fa;
}

.button.active {
  background-color: #e0f7fa;
  border: 1px solid #0d8f5e;
}

.sensor-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sensor-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: #ffffff;
  color: #2f5644;
  padding: 10px;
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
  font-size: 14px;
  font-weight: 700;
}

.unit {
  font-size: 12px;
  color: #6f897d;
  font-weight: normal;
}

.alarm-info {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-bottom: 10px;
  background-color: #f1fbf5;
  border: 1px solid #d7efdf;
  color: #2c6b48;
  padding: 10px;
  border-radius: 10px;
  font-weight: 600;
}

.btn-add {
  padding: 9px 14px;
  background: #169b66;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  justify-self: start;
}

.btn-add:hover {
  background: #118757;
}

.device-list {
  flex: 0 0 auto;
  height: 178px;
  min-height: 178px;
  max-height: 178px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-item {
  background-color: #f9fefa;
  padding: 10px;
  border-radius: 12px;
  display: grid;
  grid-template-columns: 36px 1fr;
  grid-template-areas:
    "icon detail"
    "status status"
    "actions actions";
  gap: 8px;
  border: 1px solid #ddefe3;
  border-left: 4px solid #2cb470;
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
  gap: 2px;
}

.device-id {
  font-size: 13px;
  font-weight: 700;
  color: #22764e;
}

.device-name {
  font-size: 14px;
  font-weight: 700;
}

.device-field {
  font-size: 12px;
  color: #6f8a7d;
}

.device-type {
  font-size: 12px;
  color: #6f8a7d;
}

.device-actions {
  grid-area: actions;
  display: flex;
  gap: 8px;
}

.green {
  background-color: #2fb26f;
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.green:hover {
  background-color: #289c60;
}

.red {
  background-color: #ec6666;
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.red:hover {
  background-color: #d55353;
}

.device-status {
  grid-area: status;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #587a6b;
}

.switch {
  width: 34px;
  height: 18px;
  border-radius: 15px;
  cursor: pointer;
  position: relative;
  border: 1px solid #acc5b8;
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
  background: #169b66;
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

@media (min-width: 980px) {
  .device-management-page {
    grid-template-columns: 0.95fr 1.05fr;
    gap: 14px;
    padding: 10px;
    height: auto;
  }

  .alarm-info {
    grid-template-columns: auto 1fr;
    align-items: center;
  }

  .device-item {
    grid-template-columns: 40px 1fr auto;
    grid-template-areas:
      "icon detail status"
      "icon actions actions";
  }
}
</style>
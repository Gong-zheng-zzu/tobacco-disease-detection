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
      apiBase: '/api',
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
  display: flex;
  padding: 20px;
  gap: 20px;
}

.left-section,
.right-section {
  flex: 1;
  min-width: 0;
  min-height: 500px;
  padding: 20px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
}

.left-section {
  background-color: #008b8b;
  color: white;
  height: 500px;
}

.right-section {
  background-color: #f0f8ff;
  height: 500px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 15px;
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
  gap: 10px;
  flex-shrink: 0;
}

.field-select-area {
  margin-bottom: 10px;
}

.field-select-dropdown {
  width: 100%;
  height: 36px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  padding: 0 10px;
  font-size: 14px;
  background-color: rgba(255, 255, 255, 0.9);
  color: #333;
}

.current-field-hint {
  margin-bottom: 15px;
  font-size: 13px;
  padding: 6px 10px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
}

.button {
  padding: 8px 16px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  background-color: #ffffff;
  color: #008b8b;
  font-weight: bold;
  transition: background-color 0.3s;
}

.button:hover {
  background-color: #e0f7fa;
}

.button.active {
  background-color: #e0f7fa;
  border: 2px solid #008b8b;
}

.sensor-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sensor-item {
  display: flex;
  align-items: center;
  gap: 15px;
  background-color: #ffffff;
  color: #333;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  min-height: 70px;
  flex-shrink: 0;
}

.sensor-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.sensor-icon {
  width: 40px;
  height: 40px;
}

.sensor-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.sensor-title {
  font-size: 16px;
  font-weight: bold;
  color: #008b8b;
}

.sensor-value {
  font-size: 18px;
  font-weight: bold;
}

.unit {
  font-size: 14px;
  color: #666;
  font-weight: normal;
}

.alarm-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 20px;
  background-color: #98fb98;
  padding: 10px;
  border-radius: 5px;
  font-weight: bold;
}

.btn-add {
  padding: 6px 14px;
  background: #008b8b;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-add:hover {
  background: #006666;
}

.device-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.device-item {
  background-color: #ffffff;
  padding: 15px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #32cd32;
  min-height: 70px;
  flex-shrink: 0;
}

.device-item.offline {
  border-left-color: #ff3030;
}

.device-item:hover {
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: contain;
}

.device-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.device-id {
  font-size: 16px;
  font-weight: bold;
  color: #008b8b;
}

.device-name {
  font-size: 14px;
  font-weight: bold;
}

.device-field {
  font-size: 12px;
  color: #666;
}

.device-type {
  font-size: 12px;
  color: #666;
}

.device-actions {
  display: flex;
  gap: 10px;
}

.green {
  background-color: #32cd32;
  color: white;
  padding: 8px 12px;
  border-radius: 5px;
  transition: background-color 0.3s;
}

.green:hover {
  background-color: #28a745;
}

.red {
  background-color: #ff3030;
  color: white;
  padding: 8px 12px;
  border-radius: 5px;
  transition: background-color 0.3s;
}

.red:hover {
  background-color: #dc3545;
}

.device-status {
  display: flex;
  align-items: center;
  gap: 5px;
}

.switch {
  width: 30px;
  height: 15px;
  border-radius: 15px;
  cursor: pointer;
  position: relative;
  border: 1px solid #999;
}

.switch::before {
  content: '';
  position: absolute;
  width: 13px;
  height: 13px;
  background-color: #fff;
  border-radius: 50%;
  top: 1px;
  transition: transform 0.2s;
}

.on {
  background-color: #32cd32;
}

.on::before {
  transform: translateX(15px);
}

.off {
  background-color: #ccc;
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
  padding: 24px;
  border-radius: 12px;
  min-width: 320px;
}

.modal-content h3 {
  margin: 0 0 20px;
  color: #008b8b;
}

.modal-body { margin-bottom: 20px; }

.form-row {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-row label {
  min-width: 80px;
  font-size: 14px;
}

.modal-input, .modal-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ccc;
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
  background: #008b8b;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-delete {
  background: #ff3030;
}

.btn-delete:hover {
  background: #dc3545;
}

.delete-confirm-text {
  margin: 0;
  font-size: 15px;
  color: #333;
}
</style>
<template>
  <div class="home">
    <div class="left-section">
      <div class="section-header light-green">
        <span class="section-title"><i class="icon-dot"></i>施肥概览</span>
      </div>
      <div class="chart-area">
        <div id="home-chart" class="chart-container"></div>
      </div>
      <div class="fertilizer-summary">
        <span>氮肥: {{ fertilizerData.N }} kg</span>
        <span>磷肥: {{ fertilizerData.P }} kg</span>
        <span>钾肥: {{ fertilizerData.K }} kg</span>
        <span class="update-time">更新至 {{ updateDate }}</span>
      </div>
      <div class="sensor-row">
        <div class="sensor-item">
          <img :src="soilMoistureIcon" alt="土壤湿度" class="sensor-icon">
          <div class="sensor-info">
            <span class="sensor-title">土壤湿度</span>
            <span class="sensor-value">24% <small>VWC</small></span>
          </div>
        </div>
        <div class="sensor-item">
          <img :src="temperatureIcon" alt="空气温度" class="sensor-icon">
          <div class="sensor-info">
            <span class="sensor-title">空气温度</span>
            <span class="sensor-value">25°C</span>
          </div>
        </div>
        <div class="sensor-item">
          <img :src="humidityIcon" alt="空气湿度" class="sensor-icon">
          <div class="sensor-info">
            <span class="sensor-title">空气湿度</span>
            <span class="sensor-value">65% <small>RH</small></span>
          </div>
        </div>
      </div>
    </div>

    <div class="center-section">
      <div class="section-header light-green">
        <span class="section-title"><i class="icon-dot"></i>{{ detectionMode === 'deficiency' ? '缺素识别' : '病虫害识别' }}</span>
        <div class="detection-mode-toggle">
          <button type="button" class="toggle-btn" :class="{ active: detectionMode === 'deficiency' }" @click="detectionMode = 'deficiency'">缺素检测</button>
          <button type="button" class="toggle-btn" :class="{ active: detectionMode === 'disease' }" @click="detectionMode = 'disease'">病虫害检测</button>
        </div>
      </div>
      <div class="field-select-row">
        <label>地块选择：</label>
        <select v-model="selectedFieldId" class="field-select" @change="uploadError = ''">
          <option value="">请选择地块</option>
          <option v-for="f in fieldList" :key="f.id" :value="f.id">{{ f.name || f.id + '号地块' }}</option>
        </select>
      </div>
      <div v-if="uploadError && !displayImageUrl" class="field-error-msg">{{ uploadError }}</div>
      <div class="center-body">
        <div class="camera-wrap">
          <div class="camera-box">
            <video ref="videoEl" class="camera-video" autoplay playsinline v-show="cameraActive && !displayImageUrl"></video>
            <img v-if="displayImageUrl" :src="displayImageUrl" alt="定格" class="camera-frozen">
            <canvas ref="canvasEl" class="canvas-hidden"></canvas>
            <div v-if="!cameraActive && !displayImageUrl" class="camera-placeholder">
              <img :src="add_imgIcon" alt="摄像头" class="placeholder-icon">
              <p>打开摄像头或从相册选择</p>
            </div>
          </div>
          <div class="result-area">
            <div v-if="displayImageUrl" class="result-label" :class="{ 'label-healthy': recognitionResult === '健康', 'label-deficient': recognitionResult === '缺磷', 'label-loading': recognitionResult === '识别中...', 'label-disease': recognitionResult && (recognitionResult.startsWith('检测到') || recognitionResult === '未检测到病虫害'), 'label-error': uploadError }">
              <template v-if="recognitionResult">{{ recognitionResult }}</template>
              <template v-else-if="uploadError">{{ uploadError }}</template>
            </div>
            <div v-if="recognitionExtraMessage" class="result-extra">{{ recognitionExtraMessage }}</div>
          </div>
          <div class="camera-actions">
            <template v-if="displayImageUrl">
              <button class="btn-camera" @click="retakePhoto">重新拍照</button>
            </template>
            <template v-else>
              <button v-if="!cameraActive" class="btn-camera" @click="startCamera">打开摄像头</button>
              <template v-else>
                <button class="btn-capture" @click="captureAndRecognize">拍照识别</button>
                <button class="btn-close-camera" @click="stopCamera">关闭</button>
              </template>
            </template>
            <button class="btn-upload" @click="triggerFileInput">相册</button>
            <input type="file" accept="image/*" class="upload-input" ref="fileInput" @change="handleFileUpload">
          </div>
        </div>
      </div>
    </div>

    <div class="right-section">
      <div class="weather-info">
        <div class="info-header">实时天气信息</div>
        <div class="weather-detail">
          <div class="detail-item">
            <img :src="weatherIcon" alt="天气" class="weather-icon">
            <span>当前天气: {{ weatherData.condition }}</span>
          </div>
          <div class="detail-item">
            <img :src="temperatureIcon" alt="温度" class="weather-icon">
            <span>温度: {{ weatherData.temperature }}°C</span>
          </div>
          <div class="detail-item">
            <img :src="windSpeedIcon" alt="风速" class="weather-icon">
            <span>风速: {{ weatherData.windSpeed }} km/h</span>
          </div>
          <div class="detail-item">
            <img :src="humidityIcon" alt="湿度" class="weather-icon">
            <span>湿度: {{ weatherData.humidity }}%</span>
          </div>
        </div>
      </div>
      <div class="field-list">
        <div class="section-header">常看地块</div>
        <div v-for="field in fieldList" :key="field.id" class="field-item">
          <img :src="fieldIcon" alt="地块" class="icon-field">
          <div class="field-info">
            <span class="field-name">{{ field.name || field.id + '号地块' }}</span>
            <span class="field-device">面积: {{ field.area }} m²</span>
          </div>
          <button class="view-details-btn" @click="openFieldDetail(field)">查看详情</button>
        </div>
      </div>
    </div>

    <!-- 地块详情弹窗 -->
    <div v-if="fieldDetailVisible" class="field-detail-overlay" @click.self="fieldDetailVisible = false">
      <div class="field-detail-modal">
        <div class="field-detail-header">
          <h3>{{ fieldDetailData.name || fieldDetailData.id + '号地块' }}</h3>
          <span class="field-detail-area">面积: {{ fieldDetailData.area }} m²</span>
          <button class="btn-close-modal" @click="fieldDetailVisible = false">×</button>
        </div>
        <div class="field-detail-body">
          <div class="fer-section" v-if="fieldDetailData.basicRecords?.length">
            <div class="fer-section-title">基本施肥记录</div>
            <table class="fer-table">
              <thead>
                <tr><th>生长阶段</th><th>施肥时间</th><th>氮肥(kg)</th><th>磷肥(kg)</th><th>钾肥(kg)</th><th>总量(kg)</th></tr>
              </thead>
              <tbody>
                <tr v-for="r in fieldDetailData.basicRecords" :key="r.id">
                  <td>{{ r.growth_stage_display }}</td>
                  <td>{{ r.fer_time }}</td>
                  <td>{{ r.base_n_used }}</td>
                  <td>{{ r.base_p_used }}</td>
                  <td>{{ r.base_k_used }}</td>
                  <td>{{ r.base_s_used }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="fer-section" v-if="fieldDetailData.topdressingRecords?.length">
            <div class="fer-section-title">追肥记录</div>
            <table class="fer-table">
              <thead>
                <tr><th>施肥时间</th><th>氮肥(kg)</th><th>磷肥(kg)</th><th>钾肥(kg)</th><th>类型</th></tr>
              </thead>
              <tbody>
                <tr v-for="r in fieldDetailData.topdressingRecords" :key="r.id">
                  <td>{{ r.fer_time }}</td>
                  <td>{{ r.extra_n_used }}</td>
                  <td>{{ r.extra_p_used }}</td>
                  <td>{{ r.extra_k_used }}</td>
                  <td>{{ r.combined_nutrient_type || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="!fieldDetailData.basicRecords?.length && !fieldDetailData.topdressingRecords?.length" class="fer-empty">
            暂无施肥记录
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import * as echarts from 'echarts';
import fieldIcon from '@/assets/icons/field-icon.png';
import add_imgIcon from '@/assets/icons/add_img-icon.png';
import weatherIcon from '@/assets/icons/weather_icon/weather-icon.png';
import temperatureIcon from '@/assets/icons/weather_icon/temperature-icon.png';
import windSpeedIcon from '@/assets/icons/weather_icon/wind_speed-icon.png';
import humidityIcon from '@/assets/icons/weather_icon/humidity-icon.png';
import soilMoistureIcon from '@/assets/icons/sensor_icon/soil-moisture-icon.png';

export default {
  data() {
    return {
      fieldIcon,
      add_imgIcon,
      weatherIcon,
      temperatureIcon,
      windSpeedIcon,
      humidityIcon,
      soilMoistureIcon,
      recognitionResult: '',
      recognitionExtraMessage: '',
      uploadError: '',
      displayImageUrl: '',
      selectedFieldId: '',
      cameraActive: false,
      mediaStream: null,
      fertilizerData: { N: '0.00', P: '0.00', K: '0.00' },
      updateDate: '--',
      fieldList: [],
      chartInstance: null,
      weatherData: {
        condition: '加载中...',
        temperature: '--',
        windSpeed: '--',
        humidity: '--'
      },
      fieldDetailVisible: false,
      fieldDetailData: { name: '', area: '', basicRecords: [], topdressingRecords: [] },
      detectionMode: 'deficiency' // 'deficiency' | 'disease'
    };
  },
  mounted() {
    this.initChart();
    this.loadFieldList().then(() => this.loadFertilizerData());
    this.loadWeather();
    window.addEventListener('resize', () => this.chartInstance?.resize());
  },
  beforeDestroy() {
    this.chartInstance?.dispose();
    this.stopCamera();
    window.removeEventListener('resize', () => {});
  },
  methods: {
    initChart() {
      const el = document.getElementById('home-chart');
      if (!el) return;
      this.chartInstance = echarts.init(el);
      const option = {
        title: {
          text: '施肥用量概览',
          left: 'center',
          textStyle: { fontSize: 16, color: '#2d5a3d', fontWeight: 600 }
        },
        tooltip: { trigger: 'axis' },
        legend: { data: ['氮肥', '磷肥', '钾肥'], bottom: 0, textStyle: { color: '#2d5a3d' }, selectedMode: false },
        grid: { left: '8%', right: '8%', bottom: '18%', top: '18%', containLabel: true },
        xAxis: {
          type: 'category',
          data: ['苗期', '还苗期', '伸根期', '旺长期', '成熟期'],
          axisLine: { lineStyle: { color: '#8bc34a' } },
          axisLabel: { color: '#2d5a3d' }
        },
        yAxis: {
          type: 'value',
          name: '千克/亩',
          axisLine: { lineStyle: { color: '#8bc34a' } },
          splitLine: { lineStyle: { color: 'rgba(139,195,74,0.3)' } }
        },
        series: [
          // 使用各阶段需求区间的代表值（中值）进行可视化
          { name: '氮肥', type: 'bar', data: [1.75, 0.75, 1.75, 3.5, 0], itemStyle: { color: '#66bb6a' } },
          { name: '磷肥', type: 'bar', data: [1.8, 0.5, 2.5, 4.5, 1.5], itemStyle: { color: '#81c784' } },
          { name: '钾肥', type: 'bar', data: [3.5, 1.3, 5, 10, 5], itemStyle: { color: '#a5d6a7' } }
        ]
      };
      this.chartInstance.setOption(option);
    },
    async loadFertilizerData() {
      try {
        const uid = localStorage.getItem('userId') || 1;
        const firstFieldId = this.fieldList[0]?.id ?? 1;
        const res = await axios.get(`/api/user/${uid}/field/${firstFieldId}/fer_regions/`);
        const data = res.data.data || [];
        const f = { N: '0.00', P: '0.00', K: '0.00' };
        let ferDate = '';
        data.forEach(item => {
          const t = item.combined_nutrient_type || '';
          if (t.includes('N')) f.N = item.extra_n_used ?? f.N;
          if (t.includes('P')) f.P = item.extra_p_used ?? f.P;
          if (t.includes('K')) f.K = item.extra_k_used ?? f.K;
          if (!ferDate && item.fer_time) ferDate = item.fer_time.split(' ')[0].replace(/年|月|日/g, ' ').trim();
        });
        this.fertilizerData = f;
        this.updateDate = ferDate || '--';
      } catch (e) {
        console.warn('肥料数据加载失败', e);
      }
    },
    loadWeather() {
      if (!navigator.geolocation) {
        this.weatherData.condition = '定位不支持';
        return;
      }
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords;
          try {
            const res = await axios.get(
              'https://api.open-meteo.com/v1/forecast',
              { params: {
                latitude, longitude,
                current: 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m'
              } }
            );
            const cur = res.data?.current;
            if (cur) {
              this.weatherData.temperature = Math.round(cur.temperature_2m) ?? '--';
              this.weatherData.humidity = cur.relative_humidity_2m ?? '--';
              this.weatherData.windSpeed = cur.wind_speed_10m ?? '--';
              this.weatherData.condition = this.weatherCodeToText(cur.weather_code);
            }
          } catch (e) {
            this.weatherData.condition = '获取失败';
          }
        },
        () => {
          this.weatherData.condition = '定位失败';
        }
      );
    },
    weatherCodeToText(code) {
      const map = {
        0: '晴', 1: '少云', 2: '多云', 3: '阴',
        45: '雾', 48: '雾凇',
        51: '小雨', 53: '中雨', 55: '大雨', 56: '冻雨', 57: '冻雨',
        61: '小雨', 63: '中雨', 65: '大雨', 66: '冻雨', 67: '冻雨',
        71: '小雪', 73: '中雪', 75: '大雪', 77: '雪粒',
        80: '阵雨', 81: '阵雨', 82: '大阵雨',
        85: '阵雪', 86: '大阵雪',
        95: '雷雨', 96: '雷暴', 99: '雷暴'
      };
      return map[code] ?? '--';
    },
    async loadFieldList() {
      try {
        const uid = localStorage.getItem('userId') || 1;
        const res = await axios.get(`/api/user/${uid}/fields/list/`);
        const raw = res.data.data || [];
        const seen = new Set();
        const unique = raw.filter((f) => {
          const key = f.name ?? '';
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        });
        this.fieldList = unique.slice(0, 5);
        if (!this.selectedFieldId && this.fieldList.length > 0) {
          this.selectedFieldId = this.fieldList[0].id;
        }
      } catch (e) {
        this.fieldList = [
          { id: 1, name: '1号地块', area: 1500 },
          { id: 2, name: '2号地块', area: 800 },
          { id: 3, name: '3号地块', area: 1200 }
        ];
        if (!this.selectedFieldId) this.selectedFieldId = 1;
      }
      return Promise.resolve();
    },
    async startCamera() {
      try {
        this.uploadError = '';
        this.recognitionResult = '';
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        this.mediaStream = stream;
        this.$nextTick(() => {
          const video = this.$refs.videoEl;
          if (video) {
            video.srcObject = stream;
            this.cameraActive = true;
          }
        });
      } catch (e) {
        this.uploadError = '无法访问摄像头，请允许浏览器使用相机或从相册选择图片';
      }
    },
    stopCamera() {
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(t => t.stop());
        this.mediaStream = null;
      }
      const video = this.$refs.videoEl;
      if (video) video.srcObject = null;
      this.cameraActive = false;
    },
    captureAndRecognize() {
      const uid = localStorage.getItem('userId') || 1;
      if (!this.selectedFieldId) {
        this.uploadError = '请先选择地块';
        return;
      }
      const video = this.$refs.videoEl;
      const canvas = this.$refs.canvasEl;
      if (!video || !canvas || !video.videoWidth) return;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      this.displayImageUrl = canvas.toDataURL('image/jpeg', 0.9);
      this.uploadError = '';
      this.recognitionExtraMessage = '';
      this.recognitionResult = '识别中...';
      this.stopCamera();
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const formData = new FormData();
        formData.append('image', blob, 'capture.jpg');
        formData.append('mode', this.detectionMode);
        try {
          const res = await axios.post(
            `/api/user/${uid}/field/${this.selectedFieldId}/nd/`,
            formData
          );
          this.recognitionResult = res.data.result || '识别完成';
          this.recognitionExtraMessage = res.data.message || '';
          await this.addPesticideRecordsFromDiseaseResult(res.data.result);
        } catch (err) {
          this.recognitionResult = '';
          this.recognitionExtraMessage = '';
          this.uploadError = err.response?.data?.error || '识别失败，请重试';
        }
      }, 'image/jpeg', 0.9);
    },
    /** 若为病虫害检测结果且包含“检测到: xxx”，则根据病害种类在当前地块自动添加农药记录 */
    async addPesticideRecordsFromDiseaseResult(result) {
      if (!result || typeof result !== 'string' || !result.startsWith('检测到：') && !result.startsWith('检测到:')) return;
      const raw = result.replace(/^检测到[：:]?\s*/, '').trim();
      if (!raw) return;
      const diseaseTypes = raw.split(/[、,，]/).map(s => s.trim()).filter(Boolean);
      if (diseaseTypes.length === 0) return;
      const uid = localStorage.getItem('userId') || 1;
      const fieldId = this.selectedFieldId;
      if (!fieldId) return;
      try {
        const res = await axios.post(
          `/api/user/${uid}/field/${fieldId}/pesticide_from_diseases/`,
          { disease_types: diseaseTypes }
        );
        if (res.data.code === 200 && res.data.created > 0) {
          const msg = res.data.msg || `已自动添加 ${res.data.created} 条农药记录`;
          this.recognitionExtraMessage = this.recognitionExtraMessage
            ? `${this.recognitionExtraMessage}；${msg}`
            : msg;
        }
      } catch (e) {
        console.warn('自动添加农药记录失败', e);
      }
    },
    retakePhoto() {
      this.displayImageUrl = '';
      this.recognitionResult = '';
      this.recognitionExtraMessage = '';
      this.uploadError = '';
      this.startCamera();
    },
    async openFieldDetail(field) {
      this.fieldDetailData = {
        id: field.id,
        name: field.name || field.id + '号地块',
        area: field.area ?? '—',
        basicRecords: [],
        topdressingRecords: []
      };
      this.fieldDetailVisible = true;
      const uid = localStorage.getItem('userId') || 1;
      try {
        const [basicRes, topRes] = await Promise.all([
          axios.get(`/api/user/${uid}/fer_records/${field.id}/`),
          axios.get(`/api/user/${uid}/field/${field.id}/fer_regions/`)
        ]);
        if (basicRes.data?.code === 200) this.fieldDetailData.basicRecords = basicRes.data.data || [];
        if (topRes.data?.code === 200) this.fieldDetailData.topdressingRecords = topRes.data.data || [];
      } catch (e) {
        console.warn('获取地块施肥数据失败', e);
      }
    },
    triggerFileInput() {
      this.$refs.fileInput?.click();
    },
    handleFileUpload(event) {
      const file = event.target.files?.[0];
      if (!file) return;
      const uid = localStorage.getItem('userId') || 1;
      if (!this.selectedFieldId) {
        this.uploadError = '请先选择地块';
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        this.stopCamera();
        this.displayImageUrl = e.target.result;
        this.uploadError = '';
        this.recognitionExtraMessage = '';
        this.recognitionResult = '识别中...';
        const formData = new FormData();
        formData.append('image', file);
        formData.append('mode', this.detectionMode);
        axios.post(
          `/api/user/${uid}/field/${this.selectedFieldId}/nd/`,
          formData
        )
          .then(async (res) => {
            this.recognitionResult = res.data.result || '识别完成';
            this.recognitionExtraMessage = res.data.message || '';
            await this.addPesticideRecordsFromDiseaseResult(res.data.result);
            this.$refs.fileInput.value = '';
          })
          .catch(err => {
            this.recognitionResult = '';
            this.recognitionExtraMessage = '';
            this.uploadError = err.response?.data?.error || '上传失败，请重试';
          });
      };
      reader.readAsDataURL(file);
    }
  }
};
</script>

<style scoped>
.home {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
  min-height: calc(100vh - 50px);
  align-items: stretch;
}

.left-section {
  flex: 0 0 320px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(45, 90, 61, 0.08);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.center-section {
  flex: 1;
  min-width: 360px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(45, 90, 61, 0.08);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.center-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.right-section {
  flex: 0 0 240px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.section-header {
  font-size: 15px;
  font-weight: 600;
  color: #2d5a3d;
  padding: 8px 0;
  flex-shrink: 0;
}

.section-header.light-green {
  background: linear-gradient(90deg, #66bb6a 0%, #81c784 100%);
  color: #fff;
  padding: 10px 14px;
  border-radius: 10px;
  margin: -2px -2px 0 -2px;
}

.center-section .section-header {
  margin-bottom: 2px;
}

.icon-dot {
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  display: inline-block;
  margin-right: 8px;
}

.chart-area {
  flex: 1;
  min-height: 200px;
}

#home-chart {
  width: 100%;
  height: 100%;
}

.fertilizer-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  padding: 8px 12px;
  background: #e8f5e9;
  border-radius: 10px;
  font-size: 13px;
  color: #2d5a3d;
}

.update-time {
  margin-left: auto;
  opacity: 0.9;
}

.sensor-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.sensor-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #f1f8e9;
  border-radius: 10px;
}

.sensor-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.sensor-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sensor-title { font-size: 12px; color: #558b2f; }
.sensor-value { font-size: 14px; font-weight: 600; color: #2d5a3d; }

.weather-info, .field-list {
  background: #ffffff;
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(45, 90, 61, 0.08);
}

.field-list {
  flex: 1;
  min-height: 200px;
}

.info-header {
  font-size: 14px;
  font-weight: 600;
  color: #2d5a3d;
  margin-bottom: 10px;
}

.weather-detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #e8f5e9;
  border-radius: 8px;
  font-size: 13px;
  color: #33691e;
}

.weather-icon { width: 20px; height: 20px; flex-shrink: 0; }

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #f1f8e9;
  border-radius: 10px;
  margin-bottom: 6px;
}

.field-item:last-child { margin-bottom: 0; }

.icon-field { width: 36px; height: 36px; border-radius: 8px; flex-shrink: 0; }

.field-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-name { font-size: 14px; font-weight: 600; color: #2d5a3d; }
.field-device { font-size: 12px; color: #558b2f; }

.view-details-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 8px;
  background: #66bb6a;
  color: #fff;
  font-weight: 500;
  font-size: 12px;
  cursor: pointer;
}

.view-details-btn:hover { background: #81c784; }

.camera-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  min-height: 0;
}

.camera-box {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  max-width: 380px;
  margin: 0 auto;
  background: #e8f5e9;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
}

.camera-video,
.camera-frozen {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.camera-frozen {
  position: absolute;
  inset: 0;
}

.camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #558b2f;
  font-size: 13px;
}

.placeholder-icon { width: 48px; height: 48px; opacity: 0.6; }

.canvas-hidden { display: none; }

.camera-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
}

.btn-camera, .btn-capture, .btn-close-camera, .btn-upload {
  padding: 8px 16px;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-camera, .btn-capture {
  background: #66bb6a;
  color: #fff;
}

.btn-camera:hover, .btn-capture:hover {
  background: #5cb860;
}

.btn-close-camera {
  background: #e8e8e8;
  color: #333;
}

.btn-close-camera:hover { background: #ddd; }

.btn-upload {
  background: #fff;
  color: #2d5a3d;
  border: 1px solid #81c784;
}

.btn-upload:hover {
  background: #e8f5e9;
}

.upload-input { display: none; }

.field-select-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 14px;
  color: #2d5a3d;
}

.field-select {
  flex: 1;
  max-width: 200px;
  padding: 8px 12px;
  border: 1px solid #81c784;
  border-radius: 8px;
  font-size: 14px;
  color: #2d5a3d;
  background: #fff;
}

.field-error-msg {
  font-size: 13px;
  color: #c62828;
  padding: 6px 0;
}

.result-area {
  min-height: 72px;
  width: 100%;
  max-width: 380px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.result-extra {
  font-size: 12px;
  color: #2e7d32;
  padding: 4px 10px;
  background: #e8f5e9;
  border-radius: 8px;
  max-width: 380px;
}

.detection-mode-toggle {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.toggle-btn {
  padding: 6px 14px;
  border: 1px solid rgba(255,255,255,0.6);
  border-radius: 8px;
  background: rgba(255,255,255,0.2);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.toggle-btn:hover {
  background: rgba(255,255,255,0.35);
}

.toggle-btn.active {
  background: #fff;
  color: #2d5a3d;
  border-color: #fff;
}

.center-section .section-header.light-green {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.result-label {
  width: 100%;
  max-width: 380px;
  text-align: center;
  padding: 10px 16px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
  flex-shrink: 0;
}

.label-healthy {
  background: #c8e6c9;
  color: #2e7d32;
}

.label-deficient {
  background: #ffccbc;
  color: #bf360c;
}

.label-loading {
  background: #e3f2fd;
  color: #1565c0;
}

.label-disease {
  background: #fff3e0;
  color: #e65100;
}

.label-error {
  background: #ffebee;
  color: #c62828;
  font-weight: 500;
  font-size: 14px;
}

.field-detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.field-detail-modal {
  background: #fff;
  border-radius: 12px;
  max-width: 560px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
}

.field-detail-header {
  padding: 16px 20px;
  background: linear-gradient(90deg, #66bb6a 0%, #81c784 100%);
  color: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.field-detail-header h3 { margin: 0; font-size: 18px; }
.field-detail-area { opacity: 0.9; font-size: 14px; }
.field-detail-header .btn-close-modal {
  margin-left: auto;
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255,255,255,0.3);
  color: #fff;
  font-size: 20px;
  line-height: 1;
  border-radius: 50%;
  cursor: pointer;
}
.field-detail-header .btn-close-modal:hover { background: rgba(255,255,255,0.5); }

.field-detail-body {
  padding: 16px;
  overflow-y: auto;
}

.fer-section { margin-bottom: 16px; }
.fer-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #2d5a3d;
  margin-bottom: 8px;
}

.fer-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.fer-table th, .fer-table td {
  border: 1px solid #e0e0e0;
  padding: 8px 10px;
  text-align: left;
}
.fer-table th { background: #e8f5e9; color: #2d5a3d; }
.fer-empty { color: #888; font-size: 14px; text-align: center; padding: 24px; }

@media (max-width: 1024px) {
  .home { flex-wrap: wrap; }
  .left-section { flex: 1 1 100%; }
  .center-section { flex: 1 1 100%; min-width: 0; }
  .right-section { flex: 1 1 100%; }
}

@media (max-width: 480px) {
  .weather-detail { grid-template-columns: 1fr; }
  .sensor-row { grid-template-columns: 1fr; }
}
</style>

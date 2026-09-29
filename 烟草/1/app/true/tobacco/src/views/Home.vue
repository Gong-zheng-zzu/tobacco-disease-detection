<template>
  <div class="home">
    <div class="home-top-weather">
      <div class="info-header">农田天气</div>
      <div class="weather-detail">
        <div class="detail-item">
          <img :src="weatherIcon" alt="天气" class="weather-icon">
          <span>天气: {{ weatherData.condition }}</span>
        </div>
        <div class="detail-item">
          <img :src="temperatureIcon" alt="温度" class="weather-icon">
          <span>{{ weatherData.temperature }}°C</span>
        </div>
        <div class="detail-item">
          <img :src="windSpeedIcon" alt="风速" class="weather-icon">
          <span>风速 {{ weatherData.windSpeed }} km/h</span>
        </div>
        <div class="detail-item">
          <img :src="humidityIcon" alt="湿度" class="weather-icon">
          <span>湿度 {{ weatherData.humidity }}%</span>
        </div>
      </div>
    </div>

    <div class="left-section">
      <div class="section-header light-green">
        <span class="section-title"><i class="icon-dot"></i>作业概览{{ fieldList[0]?.name ? ` · ${fieldList[0].name}` : '' }}</span>
      </div>
      <div class="chart-area">
        <div id="home-chart" class="chart-container"></div>
      </div>
      <p class="chart-note">{{ stageCoverage }}</p>
      <div class="fertilizer-summary">
        <span>氮肥: {{ fertilizerData.N }} kg</span>
        <span>磷肥: {{ fertilizerData.P }} kg</span>
        <span>钾肥: {{ fertilizerData.K }} kg</span>
        <span class="update-time">更新至 {{ updateDate }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import * as echarts from 'echarts';
import { markRaw } from 'vue';
import weatherIcon from '@/assets/icons/weather_icon/weather-icon.png';
import temperatureIcon from '@/assets/icons/weather_icon/temperature-icon.png';
import windSpeedIcon from '@/assets/icons/weather_icon/wind_speed-icon.png';
import humidityIcon from '@/assets/icons/weather_icon/humidity-icon.png';
import { API_BASE } from '@/config/api';

export default {
  data() {
    return {
      weatherIcon,
      temperatureIcon,
      windSpeedIcon,
      humidityIcon,
      fertilizerData: { N: '0.00', P: '0.00', K: '0.00' },
      updateDate: '--',
      stageCoverage: '正在读取基肥记录',
      fieldList: [],
      chartInstance: null,
      resizeHandler: null,
      weatherData: {
        condition: '加载中...',
        temperature: '--',
        windSpeed: '--',
        humidity: '--'
      }
    };
  },
  mounted() {
    this.initChart();
    this.loadFieldList().then(() => this.loadFertilizerData());
    this.loadWeather();
    this.resizeHandler = () => this.chartInstance?.resize();
    window.addEventListener('resize', this.resizeHandler);
  },
  beforeUnmount() {
    this.chartInstance?.dispose();
    window.removeEventListener('resize', this.resizeHandler);
  },
  methods: {
    initChart() {
      const el = document.getElementById('home-chart');
      if (!el) return;
      this.chartInstance = markRaw(echarts.init(el));
      const option = {
        title: {
          text: '各生育期施肥趋势',
          left: 'center',
          textStyle: { fontSize: 16, color: '#2d5a3d', fontWeight: 600 }
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const rows = params.map(item => `${item.marker}${item.seriesName}：${item.value} kg${item.data?.demo ? '（演示参考）' : ''}`);
            return `${params[0]?.axisValue || ''}<br>${rows.join('<br>')}`;
          }
        },
        legend: { data: ['氮肥', '磷肥', '钾肥'], bottom: 0, textStyle: { color: '#2d5a3d' }, selectedMode: false },
        grid: { left: '8%', right: '8%', bottom: '18%', top: '18%', containLabel: true },
        xAxis: {
          type: 'category',
          data: ['苗期', '还苗期', '伸根期', '旺长期', '成熟期'],
          axisLine: { lineStyle: { color: '#d5ded7' } },
          axisLabel: { color: '#2d5a3d', interval: 0 }
        },
        yAxis: {
          type: 'value',
          name: '千克/亩',
          axisLine: { lineStyle: { color: '#d5ded7' } },
          splitLine: { lineStyle: { color: '#e9eeea' } }
        },
        series: [
          { name: '氮肥', type: 'line', smooth: 0.35, smoothMonotone: 'x', symbolSize: 7, data: [0, 0, 0, 0, 0], lineStyle: { width: 3 }, itemStyle: { color: '#1f6f4a' } },
          { name: '磷肥', type: 'line', smooth: 0.35, smoothMonotone: 'x', symbolSize: 7, data: [0, 0, 0, 0, 0], lineStyle: { width: 3 }, itemStyle: { color: '#5d9c78' } },
          { name: '钾肥', type: 'line', smooth: 0.35, smoothMonotone: 'x', symbolSize: 7, data: [0, 0, 0, 0, 0], lineStyle: { width: 3 }, itemStyle: { color: '#b28a3f' } }
        ]
      };
      this.chartInstance.setOption(option);
    },
    async loadFertilizerData() {
      try {
        if (!this.fieldList.length) {
          this.stageCoverage = '暂无地块，添加地块后可查看施肥记录。';
          return;
        }
        const uid = localStorage.getItem('userId') || 1;
        const firstFieldId = this.fieldList[0].id;
        const [regionRes, recordRes] = await Promise.all([
          axios.get(`${API_BASE}/user/${uid}/field/${firstFieldId}/fer_regions/`),
          axios.get(`${API_BASE}/user/${uid}/fer_records/${firstFieldId}/`)
        ]);
        const data = regionRes.data.data || [];
        const records = recordRes.data.data || [];
        const f = { N: '0.00', P: '0.00', K: '0.00' };
        const byStage = { N: [0, 0, 0, 0, 0], P: [0, 0, 0, 0, 0], K: [0, 0, 0, 0, 0] };
        let ferDate = '';
        data.forEach(item => {
          const t = item.combined_nutrient_type || '';
          if (t.includes('N')) f.N = (Number(f.N) + Number(item.extra_n_used || 0)).toFixed(2);
          if (t.includes('P')) f.P = (Number(f.P) + Number(item.extra_p_used || 0)).toFixed(2);
          if (t.includes('K')) f.K = (Number(f.K) + Number(item.extra_k_used || 0)).toFixed(2);
          if (!ferDate && item.fer_time) ferDate = item.fer_time.split(' ')[0].replace(/年|月|日/g, ' ').trim();
        });
        records.forEach(item => {
          const stage = Number(item.growth_stage) - 1;
          if (stage >= 0 && stage < 5) {
            byStage.N[stage] += Number(item.base_n_used || 0);
            byStage.P[stage] += Number(item.base_p_used || 0);
            byStage.K[stage] += Number(item.base_k_used || 0);
          }
          f.N = (Number(f.N) + Number(item.base_n_used || 0)).toFixed(2);
          f.P = (Number(f.P) + Number(item.base_p_used || 0)).toFixed(2);
          f.K = (Number(f.K) + Number(item.base_k_used || 0)).toFixed(2);
          if (!ferDate && item.fer_time) ferDate = item.fer_time.split(' ')[0];
        });
        this.fertilizerData = f;
        const stageNames = ['苗期', '还苗期', '伸根期', '旺长期', '成熟期'];
        const recorded = stageNames.map((_, index) => index).filter(index =>
          byStage.N[index] + byStage.P[index] + byStage.K[index] > 0
        );
        const demoValues = { N: [28, 24, 30, 36, 31], P: [30, 22, 27, 33, 29], K: [58, 52, 64, 72, 66] };
        const makeSeries = nutrient => byStage[nutrient].map((value, index) => (
          value > 0 ? value : { value: demoValues[nutrient][index], demo: true, itemStyle: { opacity: 0.28 } }
        ));
        this.stageCoverage = recorded.length
          ? `已登记阶段：${recorded.map(index => stageNames[index]).join('、')}；浅色点为演示参考，不计入真实记录。`
          : '当前地块暂无基肥记录，图中显示演示参考数据。';
        this.chartInstance?.setOption({
          xAxis: { data: stageNames },
          series: [
            { name: '氮肥', data: makeSeries('N') },
            { name: '磷肥', data: makeSeries('P') },
            { name: '钾肥', data: makeSeries('K') }
          ]
        });
        this.updateDate = ferDate || '--';
      } catch (e) {
        console.warn('肥料数据加载失败', e);
        this.stageCoverage = '基肥记录暂时无法加载，请稍后重试。';
      }
    },
    loadWeather() {
      const fallbackWeather = async () => {
        try {
          const res = await axios.get(`${API_BASE}/weather/`, { timeout: 9000 });
          const cur = res.data?.current;
          if (cur) {
            this.weatherData.temperature = Math.round(cur.temperature_2m);
            this.weatherData.humidity = cur.relative_humidity_2m;
            this.weatherData.windSpeed = cur.wind_speed_10m;
            this.weatherData.condition = `${this.weatherCodeToText(cur.weather_code)}（郑州）`;
            return;
          }
        } catch (e) { /* The weather service can be temporarily unavailable. */ }
        this.weatherData = { condition: '暂不可用', temperature: '--', windSpeed: '--', humidity: '--' };
      };
      if (!navigator.geolocation) {
        void fallbackWeather();
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
            void fallbackWeather();
          }
        },
        () => {
          void fallbackWeather();
        },
        {
          enableHighAccuracy: false,
          timeout: 3500,
          maximumAge: 300000
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
        const res = await axios.get(`${API_BASE}/user/${uid}/fields/list/`);
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
        this.fieldList = [];
      }
      return Promise.resolve();
    },
  }
};
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 6px;
}

.home-top-weather {
  grid-column: 1 / -1;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-soft);
  padding: 12px;
}

.left-section,
.home-top-weather {
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-soft);
  padding: 12px;
}

.section-header {
  font-size: 15px;
  font-weight: 700;
  color: #1f6b44;
  margin-bottom: 10px;
}

.section-header.light-green {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  border-radius: 6px;
  padding: 10px 12px;
  margin: -2px -2px 8px;
  color: #1f6f4a;
  background: #f2f6f3;
}

.icon-dot {
  width: 8px;
  height: 8px;
  background: #c8a45c;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.chart-area {
  height: 250px;
  background: #fafbfa;
  border-radius: 12px;
  padding: 8px;
}

#home-chart {
  width: 100%;
  height: 100%;
}

.fertilizer-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
  padding: 10px;
  background: #f8faf8;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 13px;
}
.chart-note { margin: 8px 2px 0; color: #63776a; font-size: 13px; }

.update-time {
  grid-column: 1 / -1;
  color: #5f8070;
}

.info-header {
  font-size: 14px;
  font-weight: 700;
  color: #2d5a3d;
  margin-bottom: 8px;
}

.weather-detail {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 9px;
  background: #ffffff;
  border: 1px solid #e2f2e9;
  padding: 8px 9px;
  font-size: 12px;
  color: #2f6d4b;
}

.weather-icon { width: 18px; height: 18px; }

@media (min-width: 900px) {
  .home {
    gap: 14px;
    padding: 10px;
  }

  .chart-area {
    height: 280px;
  }

  .weather-detail {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>

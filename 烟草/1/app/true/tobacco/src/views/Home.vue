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
        <span class="section-title"><i class="icon-dot"></i>作业概览</span>
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
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import * as echarts from 'echarts';
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
      fieldList: [],
      chartInstance: null,
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
    window.addEventListener('resize', () => this.chartInstance?.resize());
  },
  beforeDestroy() {
    this.chartInstance?.dispose();
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
          axisLabel: { color: '#2d5a3d', interval: 0 }
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
        const [regionRes, recordRes] = await Promise.all([
          axios.get(`${API_BASE}/user/${uid}/field/${firstFieldId}/fer_regions/`),
          axios.get(`${API_BASE}/user/${uid}/fer_records/${firstFieldId}/`)
        ]);
        const data = regionRes.data.data || [];
        const records = recordRes.data.data || [];
        const f = { N: '0.00', P: '0.00', K: '0.00' };
        let ferDate = '';
        data.forEach(item => {
          const t = item.combined_nutrient_type || '';
          if (t.includes('N')) f.N = (Number(f.N) + Number(item.extra_n_used || 0)).toFixed(2);
          if (t.includes('P')) f.P = (Number(f.P) + Number(item.extra_p_used || 0)).toFixed(2);
          if (t.includes('K')) f.K = (Number(f.K) + Number(item.extra_k_used || 0)).toFixed(2);
          if (!ferDate && item.fer_time) ferDate = item.fer_time.split(' ')[0].replace(/年|月|日/g, ' ').trim();
        });
        records.forEach(item => {
          f.N = (Number(f.N) + Number(item.base_n_used || 0)).toFixed(2);
          f.P = (Number(f.P) + Number(item.base_p_used || 0)).toFixed(2);
          f.K = (Number(f.K) + Number(item.base_k_used || 0)).toFixed(2);
          if (!ferDate && item.fer_time) ferDate = item.fer_time.split(' ')[0];
        });
        this.fertilizerData = f;
        this.updateDate = ferDate || '--';
      } catch (e) {
        console.warn('肥料数据加载失败', e);
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
        } catch (e) { /* Keep a usable demo value when the weather provider is unavailable. */ }
        this.weatherData = { condition: '多云（演示）', temperature: 24, windSpeed: 8, humidity: 58 };
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
        this.fieldList = [
          { id: 1, name: '1号地块', area: 1500 },
          { id: 2, name: '2号地块', area: 800 },
          { id: 3, name: '3号地块', area: 1200 }
        ];
        if (!this.selectedFieldId) this.selectedFieldId = 1;
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
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(31, 79, 51, 0.08);
  padding: 12px;
}

.left-section,
.home-top-weather {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(31, 79, 51, 0.08);
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
  border-radius: 12px;
  padding: 10px 12px;
  margin: -2px -2px 8px;
  color: #fff;
  background: linear-gradient(100deg, #21a16c, #3fc885);
}

.icon-dot {
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.chart-area {
  height: 250px;
  background: #f7fcf9;
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
  background: #f4faf7;
  border: 1px solid #e4f3ea;
  border-radius: 12px;
  font-size: 13px;
}

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
    grid-template-columns: 1fr 1fr;
  }
}
</style>

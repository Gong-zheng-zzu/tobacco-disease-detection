<template>
  <div class="analysis-page">
    <div class="left-section">
      <div class="filter-bar">
        <div class="filter-buttons">
          <button
            class="button"
            :class="{ active: viewMode === 'all' }"
            @click="viewMode = 'all'; selectedFieldId = null"
          >
            全部地块
          </button>
          <button
            class="button"
            :class="{ active: viewMode === 'single' }"
            @click="viewMode = 'single'"
          >
            单个地块
          </button>
        </div>
        <div v-if="viewMode === 'single'" class="field-select-area inline">
          <select v-model="selectedFieldId" class="field-select-dropdown">
            <option :value="null" disabled>请选择地块</option>
            <option
              v-for="f in fieldList"
              :key="f.id"
              :value="f.id"
            >
              {{ f.name || (f.id + '号地块') }}（{{ f.area }} m²）
            </option>
          </select>
        </div>
      </div>

      <div class="current-field-hint">
        当前查看：{{ viewMode === 'all' ? '全部地块' : (selectedFieldName || '请选择地块') }}
      </div>

      <div class="chart-container">
        <div id="disease-chart"></div>
        <div class="chart-legend-custom">
          <span
            v-for="(name, i) in legendItems"
            :key="name"
            class="legend-item"
            :class="{ dimmed: !legendSelected[name] }"
            @click="toggleLegend(name)"
          >
            <i class="legend-dot" :style="{ backgroundColor: legendItemsColors[i] }"></i>
            {{ name }}
          </span>
        </div>
      </div>
    </div>

    <div class="right-section">
      <div class="report-content">
        <div class="report-title">烟草病害分析报告</div>
        <div class="report-updated">{{ reportSubtitle }}</div>
        <div class="deficiency-stats">
          <div class="stat-item">
            <div class="stat-title">白星病</div>
            <div class="stat-value">{{ diseaseStats.baixingbing }}</div>
            <div class="stat-percentage">{{ diseaseStats.baixingbing_pct }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-title">黄叶病</div>
            <div class="stat-value">{{ diseaseStats.huayebing }}</div>
            <div class="stat-percentage">{{ diseaseStats.huayebing_pct }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-title">烟青虫</div>
            <div class="stat-value">{{ diseaseStats.yanqingchong }}</div>
            <div class="stat-percentage">{{ diseaseStats.yanqingchong_pct }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-title">叶厚病</div>
            <div class="stat-value">{{ diseaseStats.yehuobing }}</div>
            <div class="stat-percentage">{{ diseaseStats.yehuobing_pct }}</div>
          </div>
        </div>
      </div>

      <div class="recent-deficiency">
        <div class="title">最近病害情况</div>
        <div class="status">{{ recentStatus }}</div>
        <div class="nutrient-levels">
          <div class="nutrient">
            <span class="nutrient-label">白星病记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{ width: barPercents.baixingbing + '%', backgroundColor: '#66BB6A' }"></div>
            </div>
            <span class="nutrient-value">{{ diseaseStats.baixingbing }}</span>
          </div>
          <div class="nutrient">
            <span class="nutrient-label">黄叶病记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{ width: barPercents.huayebing + '%', backgroundColor: '#42A5F5' }"></div>
            </div>
            <span class="nutrient-value">{{ diseaseStats.huayebing }}</span>
          </div>
          <div class="nutrient">
            <span class="nutrient-label">烟青虫记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{ width: barPercents.yanqingchong + '%', backgroundColor: '#FFA726' }"></div>
            </div>
            <span class="nutrient-value">{{ diseaseStats.yanqingchong }}</span>
          </div>
          <div class="nutrient">
            <span class="nutrient-label">叶厚病记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{ width: barPercents.yehuobing + '%', backgroundColor: '#f9595c' }"></div>
            </div>
            <span class="nutrient-value">{{ diseaseStats.yehuobing }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import * as echarts from 'echarts';
import { API_BASE } from '@/config/api';

const DISEASE_TYPES = ['白星病', '黄叶病', '烟青虫', '叶厚病'];
const SERIES_COLORS = ['#66BB6A', '#42A5F5', '#FFA726', '#f9595c'];
const SERIES_COLOR_RGBA = [
  'rgba(102, 187, 106, 0.2)',
  'rgba(66, 165, 245, 0.2)',
  'rgba(255, 167, 38, 0.2)',
  'rgba(249, 89, 92, 0.2)'
];

const DISEASE_KEY_MAP = {
  白星病: 'baixingbing',
  黄叶病: 'huayebing',
  烟青虫: 'yanqingchong',
  叶厚病: 'yehuobing'
};

export default {
  name: 'AnalysisDisease',
  data() {
    return {
      viewMode: 'all',
      fieldList: [],
      selectedFieldId: null,
      diseaseData: [],
      allDiseaseData: [],
      chartInstance: null,
      legendSelected: { 白星病: true, 黄叶病: true, 烟青虫: true, 叶厚病: true },
      legendItems: DISEASE_TYPES,
      legendItemsColors: SERIES_COLORS,
      replayChartAnimation: true,
      diseaseStats: {
        baixingbing: '--',
        baixingbing_pct: '',
        huayebing: '--',
        huayebing_pct: '',
        yanqingchong: '--',
        yanqingchong_pct: '',
        yehuobing: '--',
        yehuobing_pct: ''
      },
      reportSubtitle: '请选择地块查看数据',
      recentStatus: '暂无数据',
      barPercents: {
        baixingbing: 0,
        huayebing: 0,
        yanqingchong: 0,
        yehuobing: 0
      }
    };
  },
  computed: {
    selectedFieldName() {
      if (this.selectedFieldId == null || this.selectedFieldId === '') return '';
      const f = this.fieldList.find(x => x.id == this.selectedFieldId || String(x.id) === String(this.selectedFieldId));
      return f ? (f.name || f.id + '号地块') : '';
    }
  },
  watch: {
    viewMode() {
      this.resetChartLegend();
      this.prepareChartReplay();
      this.loadDiseases();
    },
    selectedFieldId() {
      this.resetChartLegend();
      this.prepareChartReplay();
      this.loadDiseases();
    }
  },
  mounted() {
    this.$nextTick(() => this.initChart());
    this.loadFieldList()
      .then(() => this.loadDiseases())
      .catch((e) => console.warn('AnalysisDisease mounted load failed', e));
    this._onResize = () => this.chartInstance?.resize();
    window.addEventListener('resize', this._onResize);
  },
  beforeDestroy() {
    if (this._onResize) window.removeEventListener('resize', this._onResize);
    this.chartInstance?.dispose();
  },
  methods: {
    async loadFieldList() {
      const uid = localStorage.getItem('userId') || 1;
      try {
        const res = await axios.get(`${API_BASE}/user/${uid}/fields/list/`);
        if (res.data?.code === 200) this.fieldList = res.data.data || [];
      } catch (e) {
        this.fieldList = [];
      }
      return Promise.resolve();
    },
    async fetchAllDiseaseRecords() {
      const uid = localStorage.getItem('userId') || 1;
      if (!this.fieldList.length) return [];
      const requests = this.fieldList.map((field) =>
        axios
          .get(`${API_BASE}/user/${uid}/pesticide_records/${field.id}/`)
          .then((res) => ({ fieldId: field.id, data: res.data?.data || [] }))
          .catch(() => ({ fieldId: field.id, data: [] }))
      );
      const responses = await Promise.all(requests);
      const list = [];
      responses.forEach(({ fieldId, data }) => {
        (data || []).forEach((item) => {
          const type = item?.target_pest;
          if (!DISEASE_TYPES.includes(type)) return;
          list.push({
            field_id: fieldId,
            disease_type: type,
            created_at: item?.spray_time || item?.created_at || ''
          });
        });
      });
      return list;
    },
    async loadDiseases() {
      if (this.viewMode === 'single' && (this.selectedFieldId == null || this.selectedFieldId === '')) {
        this.diseaseData = [];
        this.updateStatsAndChart(null);
        return;
      }

      if ((this.allDiseaseData || []).length === 0) {
        this.allDiseaseData = await this.fetchAllDiseaseRecords();
      }

      if (this.viewMode === 'all') {
        this.diseaseData = [...this.allDiseaseData];
      } else {
        const sid = Number(this.selectedFieldId) || this.selectedFieldId;
        this.diseaseData = (this.allDiseaseData || []).filter(
          d => Number(d.field_id) === Number(sid) || d.field_id == sid
        );
      }
      this.updateStatsAndChart(this.diseaseData);
    },
    updateStatsAndChart(data) {
      const stats = {
        baixingbing: 0,
        huayebing: 0,
        yanqingchong: 0,
        yehuobing: 0
      };
      if (data && data.length) {
        data.forEach((d) => {
          const key = DISEASE_KEY_MAP[d.disease_type];
          if (key) stats[key]++;
        });
        const total = stats.baixingbing + stats.huayebing + stats.yanqingchong + stats.yehuobing;
        this.diseaseStats = {
          baixingbing: stats.baixingbing + ' 条',
          baixingbing_pct: total ? `占比${Math.round(stats.baixingbing / total * 100)}%` : '',
          huayebing: stats.huayebing + ' 条',
          huayebing_pct: total ? `占比${Math.round(stats.huayebing / total * 100)}%` : '',
          yanqingchong: stats.yanqingchong + ' 条',
          yanqingchong_pct: total ? `占比${Math.round(stats.yanqingchong / total * 100)}%` : '',
          yehuobing: stats.yehuobing + ' 条',
          yehuobing_pct: total ? `占比${Math.round(stats.yehuobing / total * 100)}%` : ''
        };
        this.barPercents = {
          baixingbing: total ? Math.round((stats.baixingbing / total) * 100) : 0,
          huayebing: total ? Math.round((stats.huayebing / total) * 100) : 0,
          yanqingchong: total ? Math.round((stats.yanqingchong / total) * 100) : 0,
          yehuobing: total ? Math.round((stats.yehuobing / total) * 100) : 0
        };
        const nonZero = DISEASE_TYPES.filter((name) => {
          const key = DISEASE_KEY_MAP[name];
          return stats[key] > 0;
        });
        this.recentStatus = nonZero.length ? nonZero.join('、') : '无病害';
        this.reportSubtitle = this.viewMode === 'all' ? '全部地块病害汇总' : `${this.selectedFieldName} 病害记录`;
      } else {
        this.diseaseData = [];
        this.diseaseStats = {
          baixingbing: '--',
          baixingbing_pct: '',
          huayebing: '--',
          huayebing_pct: '',
          yanqingchong: '--',
          yanqingchong_pct: '',
          yehuobing: '--',
          yehuobing_pct: ''
        };
        this.barPercents = {
          baixingbing: 0,
          huayebing: 0,
          yanqingchong: 0,
          yehuobing: 0
        };
        this.reportSubtitle = this.viewMode === 'all' ? '全部地块暂无病害数据' : (this.selectedFieldId ? '该地块暂无病害数据' : '请选择地块查看数据');
        this.recentStatus = (this.viewMode === 'all' || this.selectedFieldId) ? '暂无病害记录' : '请选择地块';
      }
      this.applyChart();
    },
    getChartData() {
      const data = this.diseaseData?.length ? this.diseaseData : null;
      let dates = [];
      let baixingbingData = [];
      let huayebingData = [];
      let yanqingchongData = [];
      let yehuobingData = [];
      if (data && data.length) {
        const byDate = {};
        data.forEach((d) => {
          const dt = d.created_at;
          if (!dt) return;
          const key = String(dt).slice(0, 10);
          if (!byDate[key]) {
            byDate[key] = { baixingbing: 0, huayebing: 0, yanqingchong: 0, yehuobing: 0 };
          }
          const mapKey = DISEASE_KEY_MAP[d.disease_type];
          if (mapKey) byDate[key][mapKey]++;
        });
        const sorted = Object.keys(byDate).sort();
        sorted.forEach((k) => {
          dates.push(k);
          baixingbingData.push(byDate[k].baixingbing);
          huayebingData.push(byDate[k].huayebing);
          yanqingchongData.push(byDate[k].yanqingchong);
          yehuobingData.push(byDate[k].yehuobing);
        });
      }
      if (!dates.length) {
        dates = ['暂无数据'];
        baixingbingData = [0];
        huayebingData = [0];
        yanqingchongData = [0];
        yehuobingData = [0];
      }
      return { dates, baixingbingData, huayebingData, yanqingchongData, yehuobingData };
    },
    getChartOption() {
      const { dates, baixingbingData, huayebingData, yanqingchongData, yehuobingData } = this.getChartData();
      const seriesData = [baixingbingData, huayebingData, yanqingchongData, yehuobingData];
      const selected = this.legendSelected;
      return {
        animation: true,
        animationDuration: 900,
        animationEasing: 'cubicOut',
        animationDurationUpdate: 350,
        animationEasingUpdate: 'linear',
        title: { text: '病害情况变化图', left: 'center', textStyle: { fontSize: 22, color: '#333333', fontWeight: 'bold' }, padding: [8, 0] },
        backgroundColor: '#ffffff',
        tooltip: { trigger: 'item', backgroundColor: 'rgba(0, 0, 0, 0.85)', borderColor: '#333', textStyle: { color: '#fff', fontSize: 12 }, formatter: '{b}<br/>{a}: {c} 条' },
        legend: { show: false },
        grid: { left: '8%', right: '5%', bottom: '8%', top: '12%', containLabel: true },
        xAxis: {
          type: 'category',
          data: dates,
          animation: false,
          axisLabel: {
            formatter: (value) => {
              const s = String(value || '');
              const m = s.match(/(\d{4})[-/](\d{2})[-/](\d{2})/);
              if (m) return `${m[2]}/${m[3]}`;
              const zh = s.match(/(\d{4})年(\d{1,2})月(\d{1,2})日?/);
              if (zh) return `${String(zh[2]).padStart(2, '0')}/${String(zh[3]).padStart(2, '0')}`;
              const d = new Date(s);
              if (Number.isNaN(d.getTime())) return s;
              const mm = String(d.getMonth() + 1).padStart(2, '0');
              const dd = String(d.getDate()).padStart(2, '0');
              return `${mm}/${dd}`;
            }
          },
          axisLine: { lineStyle: { color: '#cccccc' } },
          axisTick: { alignWithLabel: true, lineStyle: { color: '#cccccc' } }
        },
        yAxis: {
          type: 'value',
          minInterval: 1,
          animation: false,
          name: '病害记录数',
          nameTextStyle: { color: '#333333', fontSize: 14, padding: [0, 0, 10, 0] },
          axisLabel: { color: '#333333', fontSize: 12, formatter: (value) => Number.isInteger(value) ? value : Math.round(value) },
          axisLine: { show: true, lineStyle: { color: '#cccccc' } },
          splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.1)', type: 'dashed' } }
        },
        series: DISEASE_TYPES.map((name, i) => {
          const visible = selected[name] !== false;
          return {
            name,
            type: 'line',
            data: seriesData[i],
            showSymbol: visible,
            symbol: 'circle',
            symbolSize: 6,
            smooth: 0.45,
            smoothMonotone: 'x',
            connectNulls: true,
            lineStyle: { color: SERIES_COLORS[i], width: 2.5, opacity: visible ? 1 : 0 },
            itemStyle: { color: SERIES_COLORS[i], borderColor: '#ffffff', borderWidth: 1.5 },
            label: { show: false },
            emphasis: { showSymbol: true },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: SERIES_COLOR_RGBA[i] },
                { offset: 1, color: 'rgba(0,0,0,0)' }
              ]),
              opacity: visible ? 1 : 0
            }
          };
        })
      };
    },
    applyChart() {
      if (!this.chartInstance) return;
      try {
        const option = this.getChartOption();
        if (this.replayChartAnimation) this.chartInstance.clear();
        this.chartInstance.setOption(option, { notMerge: true, lazyUpdate: false });
        this.replayChartAnimation = false;
      } catch (e) {
        console.warn('applyChart error', e);
      }
      this.chartInstance.resize();
    },
    resetChartLegend() {
      this.legendSelected = { 白星病: true, 黄叶病: true, 烟青虫: true, 叶厚病: true };
    },
    prepareChartReplay() {
      this.replayChartAnimation = true;
    },
    toggleLegend(name) {
      this.legendSelected = { ...this.legendSelected, [name]: !this.legendSelected[name] };
      this.applyChart();
    },
    initChart() {
      const chartDom = document.getElementById('disease-chart');
      if (!chartDom) return;
      this.chartInstance = echarts.init(chartDom);
      this.applyChart();
    }
  }
};
</script>

<style scoped>
.analysis-page {
  display: flex;
  padding: 12px 16px;
  gap: 12px;
  min-height: auto;
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
}

.left-section {
  flex: 1;
  background: linear-gradient(135deg, #66bb6a 0%, #81c784 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(45, 90, 61, 0.2);
}

.right-section {
  flex: 1;
  background-color: #ffffff;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(45, 90, 61, 0.1);
}

.filter-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.filter-buttons {
  display: flex;
  gap: 12px;
}

.button {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  background-color: #a5d6a7;
  color: #1b5e20;
  font-weight: 500;
  transition: background-color 0.3s;
}

.button:hover {
  background-color: #c8e6c9;
}

.button.active {
  background-color: #fff;
  color: #2e7d32;
}

.field-select-area.inline {
  width: 260px;
  flex-shrink: 0;
}

.field-select-dropdown {
  width: 100%;
  height: 36px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  padding: 0 10px;
  font-size: 14px;
  color: #333;
  outline: none;
}

.field-select-dropdown:focus {
  border-color: #66bb6a;
}

.current-field-hint {
  margin-bottom: 8px;
  font-size: 14px;
  padding: 6px 10px;
  background: rgba(255,255,255,0.25);
  border-radius: 8px;
}

.chart-container {
  margin-bottom: 0;
  height: 520px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  background-color: #ffffff;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

#disease-chart {
  flex: 1;
  min-height: 0;
  width: 100% !important;
}

.chart-legend-custom {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 8px 0 0;
  margin-top: 4px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.chart-legend-custom .legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  user-select: none;
  transition: opacity 0.2s, color 0.2s;
}

.chart-legend-custom .legend-item:hover {
  opacity: 0.9;
}

.chart-legend-custom .legend-item.dimmed {
  color: #999;
}

.chart-legend-custom .legend-item.dimmed .legend-dot {
  opacity: 0.35;
}

.chart-legend-custom .legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.recent-deficiency {
  padding: 12px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.title {
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: bold;
}

.status {
  font-size: 20px;
  color: #FFCA28;
  margin-bottom: 15px;
}

.report-content {
  background-color: #ffffff;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.report-title {
  margin-bottom: 10px;
  font-size: 22px;
  font-weight: bold;
  color: #333;
}

.report-updated {
  font-size: 14px;
  color: #888;
  margin-bottom: 20px;
}

.deficiency-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 20px;
  gap: 15px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
  transition: transform 0.3s;
}

.stat-item:hover {
  transform: translateY(-5px);
}

.stat-title {
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.stat-percentage {
  font-size: 14px;
  color: #888;
}

.nutrient-levels {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0 15px;
}

.nutrient {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20px;
}

.nutrient-label {
  min-width: 88px;
  font-weight: 500;
  color: #333;
}

.progress-container {
  position: relative;
  width: 100%;
  height: 18px;
  background-color: #f0f0f0;
  border-radius: 9px;
  overflow: hidden;
  flex-grow: 1;
}

.progress-bar {
  height: 100%;
  transition: width 0.3s ease;
  position: relative;
  z-index: 1;
  margin: 0;
}

.nutrient-value {
  min-width: 80px;
  text-align: right;
  color: #666;
  font-size: 14px;
}
</style>

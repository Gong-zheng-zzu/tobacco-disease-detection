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
        <p class="chart-note">按病虫记录日期累计；曲线为趋势展示，不代表连续监测。</p>
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
            <div class="stat-title">花叶病</div>
            <div class="stat-value">{{ diseaseStats.huayebing }}</div>
            <div class="stat-percentage">{{ diseaseStats.huayebing_pct }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-title">烟青虫</div>
            <div class="stat-value">{{ diseaseStats.yanqingchong }}</div>
            <div class="stat-percentage">{{ diseaseStats.yanqingchong_pct }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-title">野火病</div>
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
              <div class="progress-bar" :style="{ width: barPercents.baixingbing + '%', backgroundColor: '#1f6f4a' }"></div>
            </div>
            <span class="nutrient-value">{{ diseaseStats.baixingbing }}</span>
          </div>
          <div class="nutrient">
            <span class="nutrient-label">花叶病记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{ width: barPercents.huayebing + '%', backgroundColor: '#569276' }"></div>
            </div>
            <span class="nutrient-value">{{ diseaseStats.huayebing }}</span>
          </div>
          <div class="nutrient">
            <span class="nutrient-label">烟青虫记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{ width: barPercents.yanqingchong + '%', backgroundColor: '#b28a3f' }"></div>
            </div>
            <span class="nutrient-value">{{ diseaseStats.yanqingchong }}</span>
          </div>
          <div class="nutrient">
            <span class="nutrient-label">野火病记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{ width: barPercents.yehuobing + '%', backgroundColor: '#9d665b' }"></div>
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
import { markRaw } from 'vue';
import { API_BASE } from '@/config/api';

const DISEASE_TYPES = ['白星病', '花叶病', '烟青虫', '野火病'];
const SERIES_COLORS = ['#1f6f4a', '#569276', '#b28a3f', '#9d665b'];
const SERIES_COLOR_RGBA = [
  'rgba(31, 111, 74, 0.18)',
  'rgba(86, 146, 118, 0.18)',
  'rgba(178, 138, 63, 0.18)',
  'rgba(157, 102, 91, 0.18)'
];

const DISEASE_KEY_MAP = {
  白星病: 'baixingbing',
  花叶病: 'huayebing',
  烟青虫: 'yanqingchong',
  野火病: 'yehuobing'
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
      legendSelected: { 白星病: true, 花叶病: true, 烟青虫: true, 野火病: true },
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
  beforeUnmount() {
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
        const cumulative = { baixingbing: 0, huayebing: 0, yanqingchong: 0, yehuobing: 0 };
        sorted.forEach((k) => {
          dates.push(k);
          cumulative.baixingbing += byDate[k].baixingbing;
          cumulative.huayebing += byDate[k].huayebing;
          cumulative.yanqingchong += byDate[k].yanqingchong;
          cumulative.yehuobing += byDate[k].yehuobing;
          baixingbingData.push(cumulative.baixingbing);
          huayebingData.push(cumulative.huayebing);
          yanqingchongData.push(cumulative.yanqingchong);
          yehuobingData.push(cumulative.yehuobing);
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
        title: { text: '病害记录累计趋势', left: 'center', textStyle: { fontSize: 18, color: '#24372b', fontWeight: 600 }, padding: [8, 0] },
        backgroundColor: '#ffffff',
        tooltip: { trigger: 'item', backgroundColor: 'rgba(0, 0, 0, 0.85)', borderColor: '#333', textStyle: { color: '#fff', fontSize: 12 }, formatter: '{b}<br/>{a}: 累计 {c} 条' },
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
          name: '',
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
            smooth: 0.35,
            smoothMonotone: 'x',
            areaStyle: { color: SERIES_COLORS[i], opacity: 0.045 },
            lineStyle: { color: SERIES_COLORS[i], width: 2.5, opacity: visible ? 1 : 0 },
            itemStyle: { color: SERIES_COLORS[i], borderColor: '#ffffff', borderWidth: 1.5 },
            label: { show: false },
            emphasis: { showSymbol: true },
          };
        })
      };
    },
    applyChart() {
      if (!this.chartInstance) return;
      try {
        const option = this.getChartOption();
        this.chartInstance.setOption(option, { notMerge: true, lazyUpdate: false });
        this.replayChartAnimation = false;
      } catch (e) {
        console.warn('applyChart error', e);
      }
      this.chartInstance.resize();
    },
    resetChartLegend() {
      this.legendSelected = { 白星病: true, 花叶病: true, 烟青虫: true, 野火病: true };
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
      this.chartInstance = markRaw(echarts.init(chartDom));
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
  background: var(--color-page);
}

.left-section {
  flex: 1;
  min-width: 0;
  background: #fff;
  color: var(--color-text);
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow-soft);
}

.right-section {
  flex: 1;
  min-width: 0;
  background-color: #ffffff;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow-soft);
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
  background-color: #f2f6f3;
  color: #1f6f4a;
  font-weight: 500;
  transition: background-color 0.3s;
}

.button:hover {
  background-color: #e5eee7;
}

.button.active {
  background-color: #1f6f4a;
  color: #fff;
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
  background: #f2f6f3;
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
  box-shadow: none;
  display: flex;
  flex-direction: column;
}
.chart-note{margin:6px 0 0;text-align:center;color:#63776a;font-size:13px}

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
  background-color: #f7f9f7;
  border-radius: 8px;
}

.title {
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: bold;
}

.status {
  font-size: 20px;
  color: #755313;
  font-weight: 600;
  margin-bottom: 15px;
}

.report-content {
  padding: 8px 0 16px;
}

.report-title {
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: 600;
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
@media (max-width: 900px) {
  .analysis-page { flex-direction: column; padding: 8px; }
  .chart-container { height: 360px; }
}
@media (max-width: 560px) {
  .filter-bar { flex-direction: column; }
  .filter-buttons { width: 100%; gap: 8px; }
  .filter-buttons .button { flex: 1; padding: 8px; }
  .field-select-area.inline { width: 100%; }
  .deficiency-stats { gap: 6px; }
  .stat-item { padding: 10px 4px; }
  .nutrient-levels { padding: 0; gap: 14px; }
  .nutrient { gap: 8px; }
  .nutrient-label, .nutrient-value { min-width: 62px; }
}
</style>

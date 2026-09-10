<template>
  <div class="analysis-page">
    <!-- 左侧地块筛选区域 -->
    <div class="left-section">
      <!-- 顶部筛选工具条：左侧按钮，右侧单个地块搜索 / 列表 -->
      <div class="filter-bar">
        <!-- 地块筛选按钮 -->
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

        <!-- 单个地块时：只在右侧显示一行下拉候选框，不占用多行空间 -->
        <div v-if="viewMode === 'single'" class="field-select-area inline">
          <select
            v-model="selectedFieldId"
            class="field-select-dropdown"
          >
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

      <!-- 当前选中提示：全部地块或单个地块时都显示，便于卡片高度一致、不用翻页 -->
      <div class="current-field-hint">
        当前查看：{{ viewMode === 'all' ? '全部地块' : (selectedFieldName || '请选择地块') }}
      </div>

      <!-- 缺素变化图：自定义图例点击控制折线显隐 -->
      <div class="chart-container">
        <div id="deficiency-chart"></div>
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

    <!-- 右侧分析报告区域 -->
    <div class="right-section">
      <div class="report-content">
        <div class="report-title">烟草缺素分析报告</div>
        <div class="report-updated">{{ reportSubtitle }}</div>
        <div class="deficiency-stats">
          <div class="stat-item">
            <div class="stat-title">缺氮</div>
            <div class="stat-value">{{ deficiencyStats.N }}</div>
            <div class="stat-percentage">{{ deficiencyStats.N_pct }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-title">缺磷</div>
            <div class="stat-value">{{ deficiencyStats.P }}</div>
            <div class="stat-percentage">{{ deficiencyStats.P_pct }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-title">缺钾</div>
            <div class="stat-value">{{ deficiencyStats.K }}</div>
            <div class="stat-percentage">{{ deficiencyStats.K_pct }}</div>
          </div>
        </div>
      </div>

      <!-- 整体缺素含量柱状图 -->
      <div class="recent-deficiency">
        <div class="title">最近缺素情况</div>
        <div class="status">{{ recentStatus }}</div>
        <div class="nutrient-levels">
          <!-- 缺氮记录条数 -->
          <div class="nutrient">
            <span class="nutrient-label">缺氮记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{
                width: barPercents.N + '%',
                backgroundColor: '#4CAF50'
              }"></div>
            </div>
            <span class="nutrient-value">{{ deficiencyStats.N }}</span>
          </div>

          <!-- 缺磷记录条数 -->
          <div class="nutrient">
            <span class="nutrient-label">缺磷记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{
                width: barPercents.P + '%',
                backgroundColor: '#2196F3'
              }"></div>
            </div>
            <span class="nutrient-value">{{ deficiencyStats.P }}</span>
          </div>

          <!-- 缺钾记录条数 -->
          <div class="nutrient">
            <span class="nutrient-label">缺钾记录</span>
            <div class="progress-container">
              <div class="progress-bar" :style="{
                width: barPercents.K + '%',
                backgroundColor: '#FF9800'
              }"></div>
            </div>
            <span class="nutrient-value">{{ deficiencyStats.K }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import searchIcon from '@/assets/icons/search-icon.png';
import * as echarts from 'echarts';

const SERIES_NAMES = ['缺氮', '缺磷', '缺钾'];
const SERIES_COLORS = ['#4CAF50', '#2196F3', '#FF9800'];
const SERIES_COLOR_RGBA = ['rgba(76, 175, 80, 0.2)', 'rgba(33, 150, 243, 0.2)', 'rgba(255, 152, 0, 0.2)'];

export default {
  name: 'AnalysisPage',
  data() {
    return {
      searchIcon,
      viewMode: 'all',
      fieldList: [],
      selectedFieldId: null,
      searchKeyword: '',
      deficiencyData: [],
      allDeficiencyData: [],
      chartInstance: null,
      /** 图例选中状态：true 显示曲线，false 灰显且折线消失。由自定义图例点击 + applyChart 维护。 */
      legendSelected: { '缺氮': true, '缺磷': true, '缺钾': true },
      legendItems: SERIES_NAMES,
      legendItemsColors: SERIES_COLORS,
      replayChartAnimation: true,
      deficiencyStats: { N: '--', N_pct: '', P: '--', P_pct: '', K: '--', K_pct: '' },
      reportSubtitle: '请选择地块查看数据',
      recentStatus: '暂无数据',
      barPercents: { N: 0, P: 0, K: 0 }
    };
  },
  computed: {
    filteredFieldList() {
      if (!this.searchKeyword.trim()) return this.fieldList;
      const kw = this.searchKeyword.trim().toLowerCase();
      return this.fieldList.filter(f => {
        const name = (f.name || f.id + '号地块').toLowerCase();
        const idStr = String(f.id);
        return name.includes(kw) || idStr.includes(kw);
      });
    },
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
      this.loadDeficiencies();
    },
    selectedFieldId() {
      this.resetChartLegend();
      this.prepareChartReplay();
      this.loadDeficiencies();
    }
  },
  mounted() {
    this.$nextTick(() => this.initChart());
    this.loadFieldList()
      .then(() => this.loadDeficiencies())
      .catch((e) => console.warn('Analysis mounted load failed', e));
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
        const res = await axios.get(`/api/user/${uid}/fields/list/`);
        if (res.data?.code === 200) this.fieldList = res.data.data || [];
      } catch (e) {
        this.fieldList = [];
      }
      return Promise.resolve();
    },
    onSearchInput() {},
    selectField(f) {
      this.selectedFieldId = this.selectedFieldId === f.id ? null : f.id;
    },
    async loadDeficiencies() {
      const uid = localStorage.getItem('userId') || 1;
      if (this.viewMode === 'all') {
        if ((this.allDeficiencyData || []).length > 0) {
          this.deficiencyData = [...this.allDeficiencyData];
          this.updateStatsAndChart(this.deficiencyData);
        }
        try {
          const res = await axios.get(`/api/user/${uid}/deficiencies/`);
          const code = res.data?.code;
          const raw = res.data?.data;
          if ((code === 200 || code === undefined) && raw !== undefined) {
            const list = Array.isArray(raw) ? raw : [raw];
            this.deficiencyData = list;
            this.allDeficiencyData = list;
            this.updateStatsAndChart(this.deficiencyData);
          }
        } catch (e) {
          console.warn('loadDeficiencies failed', e);
          if (!(this.allDeficiencyData || []).length) {
            this.deficiencyData = [];
            this.updateStatsAndChart(null);
          }
        }
        return;
      }
      if (this.viewMode === 'single' && (this.selectedFieldId == null || this.selectedFieldId === '')) {
        this.deficiencyData = [];
        this.updateStatsAndChart(null);
        return;
      }
      const applySingleFilter = () => {
        const sid = Number(this.selectedFieldId) || this.selectedFieldId;
        const list = (this.allDeficiencyData || []).filter(
          d => d && (Number(d.parcel_id) === Number(sid) || d.parcel_id == sid || d.parcel == sid)
        );
        this.deficiencyData = list;
        this.updateStatsAndChart(this.deficiencyData);
      };
      if ((this.allDeficiencyData || []).length > 0) {
        applySingleFilter();
        return;
      }
      try {
        const res = await axios.get(`/api/user/${uid}/deficiencies/`);
        const code = res.data?.code;
        const raw = res.data?.data;
        if ((code === 200 || code === undefined) && raw !== undefined) {
          const list = Array.isArray(raw) ? raw : [raw];
          this.allDeficiencyData = list;
          applySingleFilter();
        } else {
          this.deficiencyData = [];
          this.updateStatsAndChart(null);
        }
      } catch (e) {
        console.warn('loadDeficiencies failed', e);
        this.deficiencyData = [];
        this.updateStatsAndChart(null);
      }
    },
    updateStatsAndChart(data) {
      const stats = { N: 0, P: 0, K: 0 };
      if (data && data.length) {
        data.forEach(d => {
          if (d.nutrient_type === 'N') stats.N++;
          else if (d.nutrient_type === 'P') stats.P++;
          else if (d.nutrient_type === 'K') stats.K++;
        });
        const total = stats.N + stats.P + stats.K;
        this.deficiencyStats = {
          N: stats.N + ' 条',
          N_pct: total ? `占比${Math.round(stats.N / total * 100)}%` : '',
          P: stats.P + ' 条',
          P_pct: total ? `占比${Math.round(stats.P / total * 100)}%` : '',
          K: stats.K + ' 条',
          K_pct: total ? `占比${Math.round(stats.K / total * 100)}%` : ''
        };
        this.barPercents = {
          N: total ? Math.round((stats.N / total) * 100) : 0,
          P: total ? Math.round((stats.P / total) * 100) : 0,
          K: total ? Math.round((stats.K / total) * 100) : 0
        };
        const types = [];
        if (stats.N) types.push('缺氮');
        if (stats.P) types.push('缺磷');
        if (stats.K) types.push('缺钾');
        this.recentStatus = types.length ? types.join('、') : '无缺素';
        this.reportSubtitle = this.viewMode === 'all' ? '全部地块缺素汇总' : `${this.selectedFieldName} 缺素记录`;
      } else {
        this.deficiencyData = [];
        this.deficiencyStats = { N: '--', N_pct: '', P: '--', P_pct: '', K: '--', K_pct: '' };
        this.barPercents = { N: 0, P: 0, K: 0 };
        this.reportSubtitle = this.viewMode === 'all' ? '全部地块暂无缺素数据' : (this.selectedFieldId ? '该地块暂无缺素数据' : '请选择地块查看数据');
        this.recentStatus = (this.viewMode === 'all' || this.selectedFieldId) ? '暂无缺素记录' : '请选择地块';
      }
      this.applyChart();
    },

    /** 从 deficiencyData 聚合出图表用的日期与三条折线数据 */
    getChartData() {
      const data = this.deficiencyData?.length ? this.deficiencyData : null;
      let dates = [], nitrogenData = [], phosphorusData = [], potassiumData = [];
      if (data && data.length) {
        const byDate = {};
        data.forEach(d => {
          const dt = d.created_at_date || d.created_at;
          if (!dt) return;
          const key = String(dt).slice(0, 10);
          if (!byDate[key]) byDate[key] = { N: 0, P: 0, K: 0 };
          if (d.nutrient_type === 'N') byDate[key].N++;
          else if (d.nutrient_type === 'P') byDate[key].P++;
          else if (d.nutrient_type === 'K') byDate[key].K++;
        });
        const sorted = Object.keys(byDate).sort();
        sorted.forEach(k => {
          dates.push(k);
          nitrogenData.push(byDate[k].N);
          phosphorusData.push(byDate[k].P);
          potassiumData.push(byDate[k].K);
        });
        if (!dates.length) {
          dates = ['暂无'];
          nitrogenData = [0];
          phosphorusData = [0];
          potassiumData = [0];
        }
      } else {
        dates = ['暂无数据'];
        nitrogenData = [0];
        phosphorusData = [0];
        potassiumData = [0];
      }
      return { dates, nitrogenData, phosphorusData, potassiumData };
    },

    /** 根据当前数据和 legendSelected 生成完整图表 option，图例与折线显隐一致 */
    getChartOption() {
      const { dates, nitrogenData, phosphorusData, potassiumData } = this.getChartData();
      const seriesData = [nitrogenData, phosphorusData, potassiumData];
      const selected = this.legendSelected;

      return {
        animation: true,
        animationDuration: 900,
        animationEasing: 'cubicOut',
        animationDurationUpdate: 350,
        animationEasingUpdate: 'linear',
        title: { text: '缺素情况变化图', left: 'center', textStyle: { fontSize: 22, color: '#333333', fontWeight: 'bold' }, padding: [8, 0] },
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
          name: '缺素记录数',
          nameTextStyle: { color: '#333333', fontSize: 14, padding: [0, 0, 10, 0] },
          axisLabel: { color: '#333333', fontSize: 12, formatter: (value) => Number.isInteger(value) ? value : Math.round(value) },
          axisLine: { show: true, lineStyle: { color: '#cccccc' } },
          splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.1)', type: 'dashed' } }
        },
        series: SERIES_NAMES.map((name, i) => {
          const visible = selected[name] !== false;
          return {
            name,
            type: 'line',
            data: seriesData[i],
            showSymbol: visible,
            symbol: 'circle',
            symbolSize: 6,
            smooth: true,
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

    /** 用当前数据和图例状态重绘图表（数据变更或图例点击后调用） */
    applyChart() {
      if (!this.chartInstance) return;
      try {
        const option = this.getChartOption();
        if (this.replayChartAnimation) {
          // 切换地块/模式时先清空，再按新数据重绘，触发从左到右的入场动画
          this.chartInstance.clear();
        }
        this.chartInstance.setOption(option, { notMerge: true, lazyUpdate: false });
        this.replayChartAnimation = false;
      } catch (e) {
        console.warn('applyChart error', e);
      }
      this.chartInstance.resize();
    },

    /** 切换地块/视图时：图例恢复为全部显示，图表随新数据由 loadDeficiencies → applyChart 重绘 */
    resetChartLegend() {
      this.legendSelected = { '缺氮': true, '缺磷': true, '缺钾': true };
    },

    /** 标记下一次绘图重播入场动画 */
    prepareChartReplay() {
      this.replayChartAnimation = true;
    },

    /** 自定义图例点击：切换该项显隐并重绘图表 */
    toggleLegend(name) {
      this.legendSelected = { ...this.legendSelected, [name]: !this.legendSelected[name] };
      this.applyChart();
    },

    /** 初始化图表 DOM（图例用自定义 HTML，不依赖 ECharts 事件） */
    initChart() {
      const chartDom = document.getElementById('deficiency-chart');
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

/* 顶部筛选工具条：按钮 + 单个地块搜索区域并排放置 */
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

.field-select-area {
  margin-bottom: 0;
}

/* 顶部并排时的宽度控制，避免撑满整行 */
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

.field-list {
  max-height: 140px;
  overflow-y: auto;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-item {
  padding: 8px 12px;
  background: rgba(255,255,255,0.2);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.field-item:hover {
  background: rgba(255,255,255,0.35);
}

.field-item.selected {
  background: #fff;
  color: #2e7d32;
}

.field-area {
  font-size: 12px;
  opacity: 0.9;
}

.field-empty {
  margin-top: 8px;
  color: rgba(255,255,255,0.8);
  font-size: 14px;
}

.current-field-hint {
  margin-bottom: 8px;
  font-size: 14px;
  padding: 6px 10px;
  background: rgba(255,255,255,0.25);
  border-radius: 8px;
}

.search-bar {
  margin-bottom: 12px;
  position: relative;
  width: 100%;
}

.search-bar input {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  background-color: #ffffff;
  transition: border-color 0.3s;
}

.search-bar input:focus {
  border-color: #66bb6a;
  outline: none;
}

.search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  cursor: pointer;
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

#deficiency-chart {
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
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 15px;
}

.stat-item {
  flex: 1;
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

/* 修改后的CSS样式 */
.nutrient-levels {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 0 15px;
}

.nutrient {
  flex-direction: row;
  align-items: center;
  gap: 20px;
}

.nutrient-label {
  min-width: 80px;
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
  /* 允许容器扩展 */
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
  /* 固定右侧数值宽度 */
  text-align: right;
  /* 右对齐 */
  color: #666;
  font-size: 14px;
}
</style>
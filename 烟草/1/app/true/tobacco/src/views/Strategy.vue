<template>
  <div class="intelligent-strategy-page">
    <!-- 左侧智能方案区域 -->
    <div class="left-section">
      <div class="field-info">
        <div class="field-number">{{ currentFieldLabel }}</div>
        <div class="field-select-row">
          <label>地块选择</label>
          <select v-model="selectedFieldId" class="field-select">
            <option v-for="f in fieldList" :key="f.id" :value="f.id">
              {{ f.name || (f.id + '号地块') }}
            </option>
          </select>
        </div>
        <div class="strategy-actions">
          <button
            type="button"
            class="strategy-btn"
            :class="{ 'is-active': activeStrategy === 'fertilizer' }"
            @click="activeStrategy = 'fertilizer'"
          >
            智能施肥方案
          </button>
          <button
            type="button"
            class="strategy-btn"
            :class="{ 'is-active': activeStrategy === 'pesticide' }"
            @click="activeStrategy = 'pesticide'"
          >
            智能施药方案
          </button>
        </div>
      </div>
      <div v-if="activeStrategy === 'fertilizer'" class="scheme-list">
        <div v-for="item in fertilizerSchemes" :key="item.name" class="scheme-item">
          <div class="scheme-title">{{ item.name }}</div>
          <div class="scheme-details">
            <div class="detail-item">
              <span>总用量</span>
              <span>{{ item.total }}</span>
            </div>
            <div class="detail-item">
              <span>{{ item.phaseLabel }}</span>
              <span>{{ item.phaseValue }}</span>
            </div>
            <div class="note">
              <span>注意事项：{{ item.note }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="scheme-list">
        <div v-for="item in pesticideSchemes" :key="item.name" class="scheme-item">
          <div class="scheme-title">{{ item.name }}</div>
          <div class="scheme-details">
            <div class="detail-item">
              <span>防治对象</span>
              <span>{{ item.target }}</span>
            </div>
            <div class="detail-item">
              <span>建议用量</span>
              <span>{{ item.dosage }}</span>
            </div>
            <div class="detail-item">
              <span>施药时期</span>
              <span>{{ item.timing }}</span>
            </div>
            <div class="note">
              <span>注意事项：{{ item.note }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="drone-link-bar">
        <router-link class="link-drone" to="/drone-path">无人机路径规划（全屏地图）</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_BASE } from '@/config/api';

// 1 亩 = 2000/3 平方米
const MU_M2 = 2000 / 3;

export default {
  data() {
    return {
      activeStrategy: 'fertilizer',
      fieldList: [],
      selectedFieldId: null,
      fieldAreaM2: 0,
      deficiencyTypes: [],
      diseaseTypes: [],
      fertilizerSchemesConfig: [
        {
          name: '磷酸二氢钾施用方案',
          nutrients: ['P', 'K'],
          perMuMin: 0.6,
          perMuMax: 1,
          unit: 'kg',
          phaseLabel: '打顶后叶面喷施',
          phaseValue: '0.2%-0.3% 浓度，连喷 2-3 次',
          note: '每 30 斤水兑 30-50g，叶片正反面均匀喷雾，改善成熟度与抗逆性。',
        },
        {
          name: '过磷酸钙施用方案',
          nutrients: ['P'],
          perMuMin: 112,
          perMuMax: 135,
          unit: 'kg',
          phaseLabel: '施用方式',
          phaseValue: '全部作基肥施用',
          note: '开沟深施 15-20cm，与土壤混匀，避免与碱性肥料混施。',
        },
        {
          name: '硫酸钾型复合肥（15-15-15）施用方案',
          nutrients: ['N', 'P', 'K'],
          perMuMin: 180,
          perMuMax: 225,
          unit: 'kg',
          phaseLabel: '施用方式',
          phaseValue: '全部作基肥施用',
          note: '选择硫酸钾型（忌氯），深施覆土，避免烧根。',
        },
        {
          name: '硝酸钾施用方案',
          nutrients: ['N', 'K'],
          perMuMin: 22,
          perMuMax: 27,
          unit: 'kg',
          phaseLabel: '施用时期',
          phaseValue: '移栽后 7-10 天施用',
          note: '离烟株 10-15cm 穴施，覆土后浇水，促进返青。',
        },
        {
          name: '硫酸钾施用方案',
          nutrients: ['K'],
          perMuMin: 45,
          perMuMax: 54,
          unit: 'kg',
          phaseLabel: '施用时期',
          phaseValue: '移栽后 25-30 天施用',
          note: '条施或穴施后培土，满足旺长期钾需求，提升烟叶品质。',
        },
      ],
      pesticideSchemesConfig: [
        {
          name: '50% 多菌灵可湿性粉剂施药方案',
          target: '白星病',
          perMu: 100,
          unit: '克',
          timing: '病害初发期叶面喷施',
          note: '连续阴雨后优先施药，间隔7-10天可补喷一次',
        },
        {
          name: '花叶病防治方案待确认',
          target: '花叶病',
          dosage: '待农技人员确认',
          timing: '确诊后确定',
          note: '请确认病因和当地防治方案后再施药',
        },
        {
          name: '4.5% 高效氯氰菊酯乳油施药方案',
          target: '烟青虫',
          perMu: 30,
          unit: '毫升',
          timing: '幼虫低龄期傍晚喷施',
          note: '与不同作用机制药剂轮换，降低抗药性风险',
        },
        {
          name: '野火病防治方案待确认',
          target: '野火病',
          dosage: '待农技人员确认',
          timing: '确诊后确定',
          note: '请确认病因和当地防治方案后再施药',
        },
      ],
    };
  },
  computed: {
    currentFieldLabel() {
      const current = this.fieldList.find(item => Number(item.id) === Number(this.selectedFieldId));
      return current?.name || (this.selectedFieldId ? `${this.selectedFieldId}号地块` : '请选择地块');
    },
    fertilizerSchemes() {
      const hasArea = this.fieldAreaM2 > 0;
      const mu = hasArea ? this.fieldAreaM2 / MU_M2 : 0;
      const deficiencySet = new Set(this.deficiencyTypes || []);
      const useAll = deficiencySet.size === 0;

      const visible = this.fertilizerSchemesConfig.filter(item => {
        if (useAll) return true;
        return item.nutrients.some(n => deficiencySet.has(n));
      });

      return visible.map(item => {
        if (item.perMuMin == null || item.perMuMax == null) return item;
        if (!hasArea) {
          return {
            ...item,
            total: `${item.perMuMin}-${item.perMuMax}${item.unit}/亩`,
          };
        }
        const minVal = (mu * item.perMuMin).toFixed(1);
        const maxVal = (mu * item.perMuMax).toFixed(1);
        return {
          ...item,
          total: `${minVal}-${maxVal}${item.unit}`,
        };
      });
    },
    pesticideSchemes() {
      const hasArea = this.fieldAreaM2 > 0;
      const mu = hasArea ? this.fieldAreaM2 / MU_M2 : 0;
      const diseaseSet = new Set(this.diseaseTypes || []);
      const visible = diseaseSet.size
        ? this.pesticideSchemesConfig.filter(item => diseaseSet.has(item.target))
        : this.pesticideSchemesConfig;
      return visible.map(item => {
        if (item.perMu == null && !item.parts) return item;
        if (!hasArea) {
          if (item.parts) {
            return { ...item, dosage: '硼肥20-30克/亩 + 磷酸二氢钾100克/亩' };
          }
          return { ...item, dosage: `${item.perMu}${item.unit}/亩` };
        }

        if (item.parts) {
          const [boron, phosph] = item.parts;
          const bMin = (mu * boron.perMuMin).toFixed(1);
          const bMax = (mu * boron.perMuMax).toFixed(1);
          const pVal = (mu * phosph.perMu).toFixed(1);
          return {
            ...item,
            dosage: `${boron.name}${bMin}-${bMax}${boron.unit} + ${phosph.name}${pVal}${phosph.unit}`,
          };
        }

        const dosage = (mu * item.perMu).toFixed(1);
        return { ...item, dosage: `${dosage}${item.unit}` };
      });
    },
  },
  mounted() {
    this.loadFieldList();
  },
  watch: {
    selectedFieldId() {
      this.loadStrategyContext();
    }
  },
  methods: {
    async loadFieldList() {
      try {
        const uid = localStorage.getItem('userId') || 1;
        const response = await axios.get(`${API_BASE}/user/${uid}/fields/list/`);
        const fields = response?.data?.data || [];
        this.fieldList = fields;
        if (this.fieldList.length && !this.selectedFieldId) {
          this.selectedFieldId = this.fieldList[0].id;
        } else {
          await this.loadStrategyContext();
        }
      } catch (error) {
        console.error('获取地块列表失败:', error);
      }
    },
    async loadStrategyContext() {
      const fieldId = Number(this.selectedFieldId);
      if (!fieldId) {
        this.fieldAreaM2 = 0;
        this.deficiencyTypes = [];
        this.diseaseTypes = [];
        return;
      }
      const current = this.fieldList.find(item => Number(item.id) === fieldId);
      const localArea = Number(current?.area);
      this.fieldAreaM2 = Number.isFinite(localArea) && localArea > 0 ? localArea : 0;

      try {
        const uid = localStorage.getItem('userId') || 1;
        const response = await axios.get(`${API_BASE}/user/${uid}/field/${fieldId}/strategy_context/`);
        const data = response?.data?.data || {};
        const area = Number(data?.field?.area);
        this.fieldAreaM2 = Number.isFinite(area) && area > 0 ? area : this.fieldAreaM2;
        this.deficiencyTypes = Array.isArray(data.deficiency_types) ? data.deficiency_types : [];
        this.diseaseTypes = Array.isArray(data.disease_types) ? data.disease_types : [];
      } catch (error) {
        console.warn('获取策略上下文失败，使用本地地块数据兜底', error);
        this.deficiencyTypes = [];
        this.diseaseTypes = [];
      }
    }
  },
};
</script>

<style scoped>
.intelligent-strategy-page {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 12px;
  background-color: #f5f7fa;
  min-height: 0;
  max-width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
  color: #263b30;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.left-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  padding: 20px;
  border: 1px solid #e3e9e4;
  border-radius: 8px;
  max-width: 100%;
  overflow: hidden;
}

.field-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 15px;
}

.field-number {
  font-size: 22px;
  font-weight: 700;
  color: #263238;
}

.field-select-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #2b4b3f;
}

.field-select {
  width: 100%;
  max-width: 360px;
  border: 1px solid #cde2d7;
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
  color: #1f4333;
}

.strategy-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.strategy-btn {
  font-size: 16px;
  font-weight: 600;
  background-color: #FFFFFF;
  color: #1f6f4a;
  border: 1px solid #b8d1c1;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.strategy-btn:hover {
  background-color: #f0f5f1;
}

.strategy-btn.is-active {
  background-color: #1f6f4a;
  color: #FFFFFF;
}

.scheme-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  padding-right: 4px;
}

.drone-link-bar {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5ebe6;
  flex-shrink: 0;
}

.link-drone {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  background: #1f6f4a;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  text-align: center;
  box-sizing: border-box;
}

.link-drone:active {
  opacity: 0.92;
}

.scheme-item {
  background-color: #fff;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e6ece7;
  box-shadow: 0 1px 2px rgba(16, 24, 40, .04);
  transition: transform 0.2s, box-shadow 0.2s;
  min-width: 0;
  word-break: break-word;
}

.scheme-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 24, 40, .08);
}

.scheme-title {
  font-size: 18px;
  font-weight: 600;
  color: #263238;
  margin-bottom: 8px;
}

.scheme-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #37474F;
}

.detail-item span:first-child {
  flex: 1;
}

.detail-item span:last-child {
  font-weight: 600;
}

.note {
  background-color: #f7f5ee;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 14px;
  color: #685735;
}

@media (max-width: 768px) {
  .intelligent-strategy-page {
    padding: 10px;
  }

  .field-number {
    font-size: 20px;
  }

  .strategy-btn {
    font-size: 14px;
  }

  .scheme-title {
    font-size: 16px;
  }

  .detail-item,
  .note {
    font-size: 12px;
  }
}

:focus-visible {
  outline: 2px solid #1f6f4a;
  outline-offset: 2px;
}
</style>

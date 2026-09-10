<template>
  <div class="intelligent-strategy-page">
    <!-- 左侧智能方案区域 -->
    <div class="left-section">
      <div class="field-info">
        <div class="field-number">1号地</div>
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
        <div class="scheme-item">
          <div class="scheme-title">磷酸二氢钾施用方案</div>
          <div class="scheme-details">
            <div class="detail-item">
              <span>总用量</span>
              <span>0.6-1kg</span>
            </div>
            <div class="detail-item">
              <span>打顶后叶面喷施</span>
              <span>0.2%-0.3% 浓度，连喷 2-3 次</span>
            </div>
            <div class="note">
              <span>注意事项：每 30 斤水兑 30-50g，叶片正反面均匀喷雾，改善成熟度与抗逆性。</span>
            </div>
          </div>
        </div>
        <div class="scheme-item">
          <div class="scheme-title">过磷酸钙施用方案</div>
          <div class="scheme-details">
            <div class="detail-item">
              <span>总用量</span>
              <span>112-135kg</span>
            </div>
            <div class="detail-item">
              <span>施用方式</span>
              <span>全部作基肥施用</span>
            </div>
            <div class="note">
              <span>注意事项：开沟深施 15-20cm，与土壤混匀，避免与碱性肥料混施。</span>
            </div>
          </div>
        </div>
        <div class="scheme-item">
          <div class="scheme-title">硫酸钾型复合肥（15-15-15）施用方案</div>
          <div class="scheme-details">
            <div class="detail-item">
              <span>总用量</span>
              <span>180-225kg</span>
            </div>
            <div class="detail-item">
              <span>施用方式</span>
              <span>全部作基肥施用</span>
            </div>
            <div class="note">
              <span>注意事项：选择硫酸钾型（忌氯），深施覆土，避免烧根。</span>
            </div>
          </div>
        </div>
        <div class="scheme-item">
          <div class="scheme-title">硝酸钾施用方案</div>
          <div class="scheme-details">
            <div class="detail-item">
              <span>总用量</span>
              <span>22-27kg</span>
            </div>
            <div class="detail-item">
              <span>施用时期</span>
              <span>移栽后 7-10 天施用</span>
            </div>
            <div class="note">
              <span>注意事项：离烟株 10-15cm 穴施，覆土后浇水，促进返青。</span>
            </div>
          </div>
        </div>
        <div class="scheme-item">
          <div class="scheme-title">硫酸钾施用方案</div>
          <div class="scheme-details">
            <div class="detail-item">
              <span>总用量</span>
              <span>45-54kg</span>
            </div>
            <div class="detail-item">
              <span>施用时期</span>
              <span>移栽后 25-30 天施用</span>
            </div>
            <div class="note">
              <span>注意事项：条施或穴施后培土，满足旺长期钾需求，提升烟叶品质。</span>
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
    </div>
    <!-- 右侧高德卫星地图底图区域 -->
    <div class="right-section">
      <div class="background-container">
        <div class="map-header-row">
          <div id="info-header" role="heading" aria-level="2">无人机路径规划</div>
          <button type="button" class="btn-show-path" :disabled="pathLoading" @click="onShowPathClick">
            {{ pathLoading ? '生成中...' : (pathPolyline ? '重新生成航迹' : '显示航迹') }}
          </button>
        </div>
        <div id="map-container" role="region" aria-label="无人机路径规划地图"></div>
      </div>
    </div>
  </div>
</template>

<script>
import AMapLoader from '@amap/amap-jsapi-loader';
import axios from 'axios';

// 1 亩 = 2000/3 平方米
const MU_M2 = 2000 / 3;

export default {
  data() {
    return {
      isDragging: false,
      offsetX: 0,
      offsetY: 0,
      mapInstance: null,
      errorMessage: null,
      pathPolyline: null,
      pathAnimationTimer: null,
      pathLoading: false,
      activeStrategy: 'fertilizer',
      fieldAreaM2: 0,
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
          name: '99% 磷酸二氢钾施药方案',
          target: '黄叶病',
          perMu: 100,
          unit: '克',
          timing: '黄叶初现时喷施',
          note: '兑水均匀喷雾，避开中午高温时段',
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
          name: '硼肥+磷酸二氢钾施药方案',
          target: '叶厚病',
          parts: [
            { name: '硼肥', perMuMin: 20, perMuMax: 30, unit: '克' },
            { name: '磷酸二氢钾', perMu: 100, unit: '克' },
          ],
          timing: '发病早期连续喷施',
          note: '两种药剂先分别溶解再混配，现配现用',
        },
      ],
      boundaryCoords: null,
      GRID_COLS: 25,
      GRID_ROWS: 25,
    };
  },
  computed: {
    pesticideSchemes() {
      const hasArea = this.fieldAreaM2 > 0;
      const mu = hasArea ? this.fieldAreaM2 / MU_M2 : 0;
      return this.pesticideSchemesConfig.map(item => {
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
    this.initMap();
    this.loadFieldAreaForNo1();
  },
  beforeDestroy() {
    if (this.pathAnimationTimer) clearInterval(this.pathAnimationTimer);
    if (this.pathPolyline) this.pathPolyline.setMap(null);
    if (this.mapInstance) {
      this.mapInstance.destroy();
      this.mapInstance = null;
    }
  },
  methods: {
    async loadFieldAreaForNo1() {
      try {
        const uid = localStorage.getItem('userId') || 1;
        const response = await axios.get(`/api/user/${uid}/fields/list/`);
        const fields = response?.data?.data || [];
        if (!fields.length) return;

        const no1Field = fields.find(f => `${f.name || ''}`.includes('1号地'))
          || fields.find(f => Number(f.id) === 1)
          || fields[0];
        const area = Number(no1Field?.area);
        this.fieldAreaM2 = Number.isFinite(area) && area > 0 ? area : 0;
      } catch (error) {
        console.error('获取1号地面积失败:', error);
      }
    },

    parsePolygon(geometry) {
      if (!geometry || typeof geometry !== 'string') {
        console.error('无效的几何数据:', geometry);
        return [];
      }
      try {
        const wkt = geometry
          .replace(/SRID=\d+;/gi, '')
          .replace(/Z|M/gi, '')
          .replace(/\s+/g, ' ')
          .replace(/,\s+/g, ',');

        const pattern = /POLYGON\s*\(\(([\d\s\.,-]+)\)\)/i;
        const matches = wkt.match(pattern);

        if (!matches || !matches[1]) {
          console.error('WKT格式解析失败:', wkt);
          return [];
        }

        const coords = matches[1]
          .split(',')
          .map(coord => {
            const [lng, lat] = coord.trim().split(/\s+/).map(Number);
            return [lng, lat].every(Number.isFinite) ? [lng, lat] : null;
          })
          .filter(Boolean);

        if (coords.length < 3) {
          console.error('多边形坐标不足:', coords);
          return [];
        }

        return coords;
      } catch (error) {
        console.error('坐标解析失败:', error);
        return [];
      }
    },

    async initMap() {
      try {
        await AMapLoader.load({
          key: '7ff0eae81ff052c84c6e5560fb230bde',
          version: '2.0',
          plugins: ['AMap.Polygon', 'AMap.Polyline', 'AMap.TileLayer', 'AMap.Scale'],
          AMapUI: { version: '1.1' },
        });

        this.mapInstance = new AMap.Map('map-container', {
          zoom: 16, // 设置高缩放级别
          center: [114.85831872, 38.10569321], // 中心点保持在路径中间
          viewMode: '3D',
          pitch: 40,
          layers: [new AMap.TileLayer.Satellite(), new AMap.TileLayer.RoadNet()],
        });

        // 添加比例尺控件
        this.mapInstance.addControl(new AMap.Scale({
          position: 'LB', // 左下角
          offset: [10, 10],
        }));

        this.boundaryCoords = await this.loadFieldData();

        // 移除 setFitView，保持手动设置的 zoom 和 center
        // this.mapInstance.setFitView(null, true, [20, 20, 20, 20]);
      } catch (error) {
        console.error('地图初始化失败:', error);
        this.errorMessage = '地图加载失败，请检查网络或API密钥';
        this.$message?.error?.(this.errorMessage);
      }
    },

    async loadFieldData() {
      try {
        const geoData = {
          geometry:
            'POLYGON ((114.8575 38.1069, 114.8579 38.1062, 114.8577 38.1052, 114.8582 38.1048, 114.8592 38.1050, 114.8599 38.1048, 114.8598 38.1058, 114.8594 38.1065, 114.8588 38.1068, 114.8580 38.1069, 114.8575 38.1069))',
        };

        const boundaryCoords = this.parsePolygon(geoData.geometry);
        if (boundaryCoords.length >= 3) {
          new AMap.Polygon({
            path: boundaryCoords,
            strokeWeight: 2,
            strokeColor: '#FF0000',
            fillColor: '#FF000030',
            fillOpacity: 0.3,
            map: this.mapInstance,
          });
          return boundaryCoords;
        }
        console.warn('地块边界坐标无效');
        return [];
      } catch (error) {
        console.error('地块数据加载失败:', error);
        return [];
      }
    },

    pointInPolygon([lng, lat], polygon) {
      let inside = false;
      const n = polygon.length;
      for (let i = 0, j = n - 1; i < n; j = i++) {
        const [xi, yi] = polygon[i];
        const [xj, yj] = polygon[j];
        if (((yi > lat) !== (yj > lat)) && (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi)) {
          inside = !inside;
        }
      }
      return inside;
    },

    astar(grid, start, goal, rows, cols) {
      const heuristic = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
      const getKey = (r, c) => r * cols + c;
      const openSet = [[0, start[0], start[1]]];
      const cameFrom = new Map();
      const gScore = new Map();
      gScore.set(getKey(start[0], start[1]), 0);

      const dirs = [[0, 1], [1, 0], [0, -1], [-1, 0], [1, 1], [1, -1], [-1, -1], [-1, 1]];

      while (openSet.length > 0) {
        openSet.sort((a, b) => a[0] - b[0]);
        const [f, r, c] = openSet.shift();
        if (r === goal[0] && c === goal[1]) {
          const path = [];
          let cur = [r, c];
          while (cur) {
            path.unshift(cur);
            cur = cameFrom.get(getKey(cur[0], cur[1]));
          }
          return path;
        }
        const key = getKey(r, c);
        const g = gScore.get(key) ?? Infinity;
        for (const [dr, dc] of dirs) {
          const nr = r + dr;
          const nc = c + dc;
          if (nr < 0 || nr >= rows || nc < 0 || nc >= cols || !grid[nr][nc]) continue;
          const cost = (dr !== 0 && dc !== 0) ? 1.414 : 1;
          const nkey = getKey(nr, nc);
          const ng = g + cost;
          if (ng < (gScore.get(nkey) ?? Infinity)) {
            cameFrom.set(nkey, [r, c]);
            gScore.set(nkey, ng);
            openSet.push([ng + heuristic([nr, nc], goal), nr, nc]);
          }
        }
      }
      return [];
    },

    generateCoveragePath(boundaryCoords) {
      if (!boundaryCoords || boundaryCoords.length < 3) return [];

      const lngs = boundaryCoords.map(c => c[0]);
      const lats = boundaryCoords.map(c => c[1]);
      const minLng = Math.min(...lngs);
      const maxLng = Math.max(...lngs);
      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);

      const cols = this.GRID_COLS;
      const rows = this.GRID_ROWS;
      const dLng = (maxLng - minLng) / (cols - 1) || 0.0001;
      const dLat = (maxLat - minLat) / (rows - 1) || 0.0001;

      const grid = [];
      const cellToCoord = [];
      for (let r = 0; r < rows; r++) {
        grid[r] = [];
        cellToCoord[r] = [];
        for (let c = 0; c < cols; c++) {
          const lng = minLng + c * dLng;
          const lat = minLat + r * dLat;
          grid[r][c] = this.pointInPolygon([lng, lat], boundaryCoords) ? 1 : 0;
          cellToCoord[r][c] = [lng, lat];
        }
      }

      const rowCells = [];
      for (let r = rows - 1; r >= 0; r--) {
        const cells = [];
        for (let c = 0; c < cols; c++) {
          if (grid[r][c]) cells.push([r, c]);
        }
        if (cells.length) rowCells.push({ row: r, cells });
      }

      const waypoints = [];
      for (let i = 0; i < rowCells.length; i++) {
        const { cells } = rowCells[i];
        const ordered = i % 2 === 0 ? cells : [...cells].reverse();
        waypoints.push(...ordered);
      }

      const fullPath = [];
      fullPath.push(cellToCoord[waypoints[0][0]][waypoints[0][1]]);
      for (let i = 1; i < waypoints.length; i++) {
        const from = waypoints[i - 1];
        const to = waypoints[i];
        const segment = this.astar(grid, from, to, rows, cols);
        for (let k = 1; k < segment.length; k++) {
          const [rr, cc] = segment[k];
          fullPath.push(cellToCoord[rr][cc]);
        }
      }
      return fullPath;
    },

    async onShowPathClick() {
      if (!this.boundaryCoords || this.boundaryCoords.length < 3) return;
      this.pathLoading = true;
      try {
        await this.loadDronePath(this.boundaryCoords);
      } finally {
        this.pathLoading = false;
      }
    },

    async loadDronePath(boundaryCoords) {
      try {
        let pathCoords = [];
        if (boundaryCoords && boundaryCoords.length >= 3) {
          pathCoords = this.generateCoveragePath(boundaryCoords);
        }
        if (pathCoords.length < 2) {
          console.warn('无人机路径坐标不足，跳过渲染');
          return;
        }

        if (this.pathPolyline) this.pathPolyline.setMap(null);

        this.pathPolyline = new AMap.Polyline({
          path: [pathCoords[0]],
          strokeColor: '#00FF00',
          strokeOpacity: 0.9,
          strokeWeight: 6,
          lineJoin: 'round',
          lineCap: 'round',
          showDir: true,
          dirColor: '#FFFFFF',
          dirOpacity: 0.9,
          map: this.mapInstance,
        });

        this.animatePath(pathCoords);
      } catch (error) {
        console.error('无人机路径加载失败:', error);
      }
    },

    animatePath(pathCoords) {
      if (this.pathAnimationTimer) clearInterval(this.pathAnimationTimer);
      let idx = 1;
      const interval = Math.max(15, Math.min(80, Math.floor(2000 / pathCoords.length)));
      this.pathAnimationTimer = setInterval(() => {
        if (idx >= pathCoords.length) {
          clearInterval(this.pathAnimationTimer);
          this.pathAnimationTimer = null;
          return;
        }
        const segment = pathCoords.slice(0, idx + 1);
        this.pathPolyline.setPath(segment);
        idx++;
      }, interval);
    },
  },
};
</script>

<style scoped>
.intelligent-strategy-page {
  display: flex;
  gap: 15px;
  padding: 15px;
  background-color: #F5F7FA;
  min-height: 100vh;
  font-family: 'Inter', 'Roboto', sans-serif;
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.left-section {
  flex: 1;
  background-color: #FFE4E1;
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
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

.strategy-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.strategy-btn {
  font-size: 16px;
  font-weight: 600;
  background-color: #FFFFFF;
  color: #008B8B;
  border: 1px solid #008B8B;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.strategy-btn:hover {
  background-color: #E0F7FA;
}

.strategy-btn.is-active {
  background-color: #008B8B;
  color: #FFFFFF;
}

.scheme-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 520px;
  overflow-y: auto;
  padding-right: 4px;
}

.scheme-item {
  background-color: #FFFFFF;
  padding: 12px;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.scheme-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
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
  background-color: #FFF3E0;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 14px;
  color: #EF6C00;
}

.right-section {
  flex: 1;
}

.background-container {
  background-color: #008B8B;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  transition: box-shadow 0.3s;
}

.background-container:hover {
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.map-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

#info-header {
  color: #FFFFFF;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.btn-show-path {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #fff;
  color: #008B8B;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
}

.btn-show-path:hover:not(:disabled) {
  background: #e0f7fa;
}

.btn-show-path:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

#map-container {
  width: 100%;
  height: calc(100% - 52px);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

@media (max-width: 768px) {
  .intelligent-strategy-page {
    flex-direction: column;
    padding: 10px;
  }

  .left-section,
  .right-section {
    flex: none;
    width: 100%;
    margin-right: 0;
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

  .scheme-list {
    max-height: none;
    overflow-y: visible;
    padding-right: 0;
  }

  .detail-item,
  .note {
    font-size: 12px;
  }

  .background-container {
    padding: 12px;
  }

  .map-header-row { flex-wrap: wrap; }
  #info-header { font-size: 18px; }
  #map-container { height: 50vh; }
}

:focus {
  outline: 2px solid #4DB6AC;
  outline-offset: 2px;
}
</style>
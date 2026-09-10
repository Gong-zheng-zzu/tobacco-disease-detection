<template>
  <div class="drone-path-page">
    <div class="background-container">
      <div class="map-header-row">
        <div class="page-title" role="heading" aria-level="2">无人机路径规划</div>
        <button type="button" class="btn-show-path" :disabled="pathLoading" @click="onShowPathClick">
          {{ pathLoading ? '生成中...' : (pathPolyline ? '重新生成航迹' : '显示航迹') }}
        </button>
      </div>
      <div id="map-container-drone" role="region" aria-label="无人机路径规划地图"></div>
    </div>
  </div>
</template>

<script>
import AMapLoader from '@amap/amap-jsapi-loader';

export default {
  name: 'DronePath',
  data() {
    return {
      mapInstance: null,
      errorMessage: null,
      pathPolyline: null,
      pathAnimationTimer: null,
      pathLoading: false,
      boundaryCoords: null,
      GRID_COLS: 25,
      GRID_ROWS: 25,
    };
  },
  mounted() {
    this.initMap();
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

        this.mapInstance = new AMap.Map('map-container-drone', {
          zoom: 16,
          center: [114.85831872, 38.10569321],
          viewMode: '3D',
          pitch: 40,
          layers: [new AMap.TileLayer.Satellite(), new AMap.TileLayer.RoadNet()],
        });

        this.mapInstance.addControl(new AMap.Scale({
          position: 'LB',
          offset: [10, 10],
        }));

        this.boundaryCoords = await this.loadFieldData();
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
.drone-path-page {
  padding: 10px;
  box-sizing: border-box;
  max-width: 100%;
  min-height: 0;
}

.background-container {
  background-color: #008b8b;
  width: 100%;
  min-height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
}

.map-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.page-title {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.btn-show-path {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #fff;
  color: #008b8b;
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

#map-container-drone {
  width: 100%;
  flex: 1;
  min-height: 52vh;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

@media (min-width: 900px) {
  #map-container-drone {
    min-height: 60vh;
  }
}
</style>

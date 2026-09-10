<template>
  <div class="recognition-page">
    <div class="recognition-card">
      <div class="section-header light-green">
        <span class="section-title"><i class="icon-dot"></i>{{ detectionMode === 'deficiency' ? '缺素识别中心' : '病虫害识别中心' }}</span>
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
</template>

<script>
import axios from 'axios';
import add_imgIcon from '@/assets/icons/add_img-icon.png';
import { API_BASE } from '@/config/api';

export default {
  name: 'RecognitionPage',
  data() {
    return {
      add_imgIcon,
      recognitionResult: '',
      recognitionExtraMessage: '',
      uploadError: '',
      displayImageUrl: '',
      selectedFieldId: '',
      cameraActive: false,
      mediaStream: null,
      fieldList: [],
      detectionMode: 'deficiency'
    };
  },
  mounted() {
    this.loadFieldList();
  },
  beforeDestroy() {
    this.stopCamera();
  },
  methods: {
    async loadFieldList() {
      try {
        const uid = localStorage.getItem('userId') || 1;
        const res = await axios.get(`${API_BASE}/user/${uid}/fields/list/`);
        const raw = res.data.data || [];
        this.fieldList = raw.slice(0, 10);
        if (!this.selectedFieldId && this.fieldList.length > 0) {
          this.selectedFieldId = this.fieldList[0].id;
        }
      } catch (e) {
        this.fieldList = [
          { id: 1, name: '1号地块' },
          { id: 2, name: '2号地块' }
        ];
        if (!this.selectedFieldId) this.selectedFieldId = 1;
      }
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
            `${API_BASE}/user/${uid}/field/${this.selectedFieldId}/nd/`,
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
    async addPesticideRecordsFromDiseaseResult(result) {
      if (!result || typeof result !== 'string' || (!result.startsWith('检测到：') && !result.startsWith('检测到:'))) return;
      const raw = result.replace(/^检测到[：:]?\s*/, '').trim();
      if (!raw) return;
      const diseaseTypes = raw.split(/[、,，]/).map(s => s.trim()).filter(Boolean);
      if (diseaseTypes.length === 0) return;
      const uid = localStorage.getItem('userId') || 1;
      const fieldId = this.selectedFieldId;
      if (!fieldId) return;
      try {
        const res = await axios.post(
          `${API_BASE}/user/${uid}/field/${fieldId}/pesticide_from_diseases/`,
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
        axios.post(`${API_BASE}/user/${uid}/field/${this.selectedFieldId}/nd/`, formData)
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
.recognition-page {
  padding: 8px;
}

.recognition-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(31, 79, 51, 0.08);
  padding: 14px;
}

.section-header.light-green {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 10px;
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

.detection-mode-toggle {
  margin-left: auto;
  display: flex;
  gap: 6px;
}

.toggle-btn {
  border: 1px solid rgba(255, 255, 255, 0.66);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 12px;
  padding: 6px 10px;
}

.toggle-btn.active {
  color: #246d45;
  background: #fff;
  border-color: #fff;
}

.field-select-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 10px;
  color: #2d5a3d;
}

.field-select {
  width: 100%;
  max-width: 380px;
  padding: 10px 12px;
  border: 1px solid #cde9da;
  border-radius: 10px;
  font-size: 14px;
  color: #24563b;
  background: #f8fdf9;
}

.field-error-msg {
  color: #d84b4b;
  font-size: 13px;
  margin-bottom: 8px;
}

.camera-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.camera-box {
  position: relative;
  width: 100%;
  max-width: 420px;
  aspect-ratio: 1;
  border-radius: 14px;
  overflow: hidden;
  background: #f1faf5;
  border: 1px dashed #b8dfca;
}

.camera-video,
.camera-frozen {
  width: 100%;
  height: 100%;
  object-fit: cover;
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
  color: #5c8770;
  gap: 6px;
  font-size: 13px;
}

.placeholder-icon { width: 44px; height: 44px; opacity: 0.75; }
.canvas-hidden, .upload-input { display: none; }

.camera-actions {
  display: grid;
  width: 100%;
  max-width: 420px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.btn-camera, .btn-capture, .btn-close-camera, .btn-upload {
  border-radius: 10px;
  border: none;
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 600;
}

.btn-camera, .btn-capture {
  background: #26a76f;
  color: #fff;
}

.btn-upload {
  background: #effaf3;
  color: #1f6b44;
  border: 1px solid #bee3cc;
}

.btn-close-camera {
  background: #f1f3f5;
  color: #4c5962;
}

.result-area {
  width: 100%;
  max-width: 420px;
  min-height: 62px;
}

.result-label {
  border-radius: 10px;
  text-align: center;
  padding: 10px;
  font-size: 14px;
  font-weight: 700;
}

.result-extra {
  margin-top: 6px;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  background: #f4faf7;
  color: #2b7b4f;
}

.label-healthy { background: #daf6e6; color: #1f8a53; }
.label-deficient { background: #ffe8dc; color: #cf5a2a; }
.label-loading { background: #e6f2ff; color: #2d70b7; }
.label-disease { background: #fff2de; color: #c4721e; }
.label-error { background: #ffe8ea; color: #d24f58; }
</style>

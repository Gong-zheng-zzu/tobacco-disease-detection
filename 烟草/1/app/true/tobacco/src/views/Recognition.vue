<template>
  <div class="recognition-page">
    <div class="recognition-card">
      <div class="section-header light-green">
        <span class="section-title"><i class="icon-dot"></i>{{ isPlantProtection ? '病虫害识别' : '缺素识别' }}</span>
      </div>

      <div class="field-select-row">
        <label>地块选择：</label>
        <select v-model="selectedFieldId" class="field-select" @change="uploadError = ''">
          <option value="">请选择地块</option>
          <option v-for="f in fieldList" :key="f.id" :value="f.id">{{ f.name || f.id + '号地块' }}</option>
        </select>
      </div>

      <div class="demo-samples">
        <div class="demo-title">演示样本（点击即可识别）</div>
        <button v-for="sample in demoSamples" :key="sample.name" class="demo-sample" type="button" @click="useDemoSample(sample)">
          <img :src="sample.src" :alt="sample.label">
          <span>{{ sample.label }}</span>
        </button>
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
          <div class="result-heading">识别结果</div>
          <div v-if="!displayImageUrl && !uploadError" class="result-empty">选择演示样本，或上传叶片照片开始识别</div>
          <div v-if="displayImageUrl" class="result-label" :class="{ 'label-healthy': recognitionResult === '图片提示：健康', 'label-loading': recognitionResult === '识别中...', 'label-disease': recognitionResult && recognitionResult.startsWith('图片提示：'), 'label-error': uploadError }">
            <template v-if="recognitionResult">{{ recognitionResult }}</template>
            <template v-else-if="uploadError">{{ uploadError }}</template>
          </div>
          <div v-if="resultScores.length" class="score-list">
            <div class="result-subtitle">模型分数 <small>非准确率</small></div>
            <div v-for="item in resultScores" :key="item.name" class="score-row">
              <div><span>{{ item.name }}</span><strong>{{ item.percent }}%</strong></div>
              <div class="score-track"><span :style="{ width: item.percent + '%' }"></span></div>
            </div>
          </div>
          <p v-if="resultAdvice" class="result-advice">{{ resultAdvice }}</p>
          <p v-if="recordMessage" class="result-record">{{ recordMessage }}</p>
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

      <form v-if="!isPlantProtection" class="verification-form" @submit.prevent="submitConfirmedDeficiency">
        <div class="verification-title">缺素复核记录</div>
        <div class="verification-fields">
          <label>确认结果
            <select v-model="confirmedNutrient" required>
              <option value="">请选择</option>
              <option value="N">缺氮</option>
              <option value="P">缺磷</option>
              <option value="K">缺钾</option>
            </select>
          </label>
          <label>依据来源
            <select v-model="verificationSource" required>
              <option value="">请选择</option>
              <option value="lab_report">检测报告</option>
              <option value="expert_review">专家复核</option>
            </select>
          </label>
          <label class="reference-field">报告编号或复核人及日期
            <input v-model.trim="verificationReference" maxlength="256" required placeholder="填写可核对的依据">
          </label>
        </div>
        <label class="verification-check"><input v-model="verificationAcknowledged" type="checkbox" required> 我已核对上述依据</label>
        <button class="btn-confirm" type="submit" :disabled="confirmBusy || !selectedFieldId">{{ confirmBusy ? '保存中...' : '保存确认结果' }}</button>
        <p v-if="confirmationMessage" class="confirmation-message" role="status">{{ confirmationMessage }}</p>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import add_imgIcon from '@/assets/icons/add_img-icon.png';
import { API_BASE } from '@/config/api';

export default {
  name: 'RecognitionPage',
  computed: {
    isPlantProtection() { return localStorage.getItem('activeRole') === 'plant_protection'; }
  },
  data() {
    return {
      add_imgIcon,
      recognitionResult: '',
      recognitionExtraMessage: '',
      resultScores: [],
      resultAdvice: '',
      recordMessage: '',
      uploadError: '',
      displayImageUrl: '',
      selectedFieldId: '',
      cameraActive: false,
      mediaStream: null,
      fieldList: [],
      confirmedNutrient: '',
      verificationSource: '',
      verificationReference: '',
      verificationAcknowledged: false,
      confirmBusy: false,
      confirmationMessage: '',
      demoSamples: [
        { name: 'white_spot_1', label: '白星病', src: './demo-images/white_spot_1.jpg' },
        { name: 'mosaic_1', label: '花叶病', src: './demo-images/mosaic_1.jpg' },
        { name: 'wildfire_1', label: '野火病', src: './demo-images/wildfire_1.jpg' },
        { name: 'tobacco_budworm_1', label: '烟青虫', src: './demo-images/tobacco_budworm_1.jpg' }
      ]
    };
  },
  mounted() {
    this.loadFieldList();
  },
  beforeUnmount() {
    this.stopCamera();
  },
  methods: {
    clearResultDetails() {
      this.resultScores = [];
      this.resultAdvice = '';
      this.recordMessage = '';
    },
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
        this.fieldList = [];
        this.uploadError = '地块加载失败，请检查网络连接';
      }
    },
    async startCamera() {
      try {
        this.uploadError = '';
        this.recognitionResult = '';
        this.clearResultDetails();
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
      this.clearResultDetails();
      this.recognitionResult = '识别中...';
      this.stopCamera();
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const formData = new FormData();
        formData.append('image', blob, 'capture.jpg');
        try {
          const res = await axios.post(
            `${API_BASE}/user/${uid}/field/${this.selectedFieldId}/unified_detect/`,
            formData
          );
          await this.showDetectionResult(res.data);
        } catch (err) {
          this.recognitionResult = '';
          this.recognitionExtraMessage = '';
          this.uploadError = err.response?.data?.error || '识别失败，请重试';
        }
      }, 'image/jpeg', 0.9);
    },
    async showDetectionResult(data) {
      this.clearResultDetails();
      const result = data?.result || {};
      const detected = [...(result.diseases || [])];
      if (result.is_deficiency_k && !this.isPlantProtection) detected.push('疑似缺钾');
      this.recognitionResult = detected.length ? `图片提示：${detected.join('、')}` : result.is_healthy ? '图片提示：健康' : '未检测到明确问题';
      this.resultScores = Object.entries(result.confidence || {})
        .filter(([name]) => !this.isPlantProtection || name !== '缺钾')
        .filter(([, score]) => Number.isFinite(Number(score)))
        .map(([name, score]) => ({ name, percent: Math.max(0, Math.min(100, Number(score) * 100)).toFixed(1) }));
      const message = this.isPlantProtection
        ? (result.diseases?.length ? '请结合现场情况复核病虫害结果' : '未发现明确病虫害，请继续观察')
        : result.is_deficiency_k ? '缺素结论需检测报告或专家复核' : data?.message;
      this.resultAdvice = message || '';
      await this.addPesticideRecordsFromDiseaseResult(result.diseases || []);
    },
    async addPesticideRecordsFromDiseaseResult(diseaseTypes) {
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
          this.recordMessage = msg;
        }
      } catch (e) {
        console.warn('自动添加农药记录失败', e);
      }
    },
    async submitConfirmedDeficiency() {
      if (!this.selectedFieldId || !this.verificationAcknowledged || this.confirmBusy) return;
      const uid = localStorage.getItem('userId');
      const token = localStorage.getItem('token');
      if (!uid || !token) {
        this.confirmationMessage = '请重新登录后提交';
        return;
      }
      this.confirmBusy = true;
      this.confirmationMessage = '';
      try {
        const res = await axios.post(
          `${API_BASE}/user/${uid}/field/${this.selectedFieldId}/deficiencies/confirmed/`,
          {
            nutrient_type: this.confirmedNutrient,
            verification_source: this.verificationSource,
            verification_reference: this.verificationReference
          },
          { headers: { 'X-User-Token': token } }
        );
        this.confirmationMessage = res.data.message || '确认结果已保存';
        this.verificationReference = '';
        this.verificationAcknowledged = false;
      } catch (err) {
        this.confirmationMessage = err.response?.data?.error || '保存失败，请检查网络后重试';
      } finally {
        this.confirmBusy = false;
      }
    },
    retakePhoto() {
      this.displayImageUrl = '';
      this.recognitionResult = '';
      this.recognitionExtraMessage = '';
      this.uploadError = '';
      this.clearResultDetails();
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
        this.clearResultDetails();
        this.recognitionResult = '识别中...';
        const formData = new FormData();
        formData.append('image', file);
        axios.post(`${API_BASE}/user/${uid}/field/${this.selectedFieldId}/unified_detect/`, formData)
          .then(async (res) => {
            await this.showDetectionResult(res.data);
            this.$refs.fileInput.value = '';
          })
          .catch(err => {
            this.recognitionResult = '';
            this.recognitionExtraMessage = '';
            this.uploadError = err.response?.data?.error || '上传失败，请重试';
          });
      };
      reader.readAsDataURL(file);
    },
    async useDemoSample(sample) {
      if (!this.selectedFieldId) {
        this.uploadError = '请先选择地块';
        return;
      }
      try {
        const response = await fetch(sample.src);
        if (!response.ok) throw new Error('演示样本不可用');
        const blob = await response.blob();
        const file = new File([blob], `${sample.name}.jpg`, { type: blob.type || 'image/jpeg' });
        await this.handleDemoFile(file);
      } catch (e) {
        this.uploadError = '演示样本加载失败，请检查网络';
      }
    },
    async handleDemoFile(file) {
      const uid = localStorage.getItem('userId') || 1;
      this.stopCamera();
      this.displayImageUrl = URL.createObjectURL(file);
      this.uploadError = '';
      this.recognitionExtraMessage = '';
      this.clearResultDetails();
      this.recognitionResult = '识别中...';
      const formData = new FormData();
      formData.append('image', file);
      try {
        const res = await axios.post(`${API_BASE}/user/${uid}/field/${this.selectedFieldId}/unified_detect/`, formData);
        await this.showDetectionResult(res.data);
      } catch (err) {
        this.recognitionResult = '';
        this.uploadError = err.response?.data?.error || '识别失败，请重试';
      }
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
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow-soft);
  padding: 14px;
}

.section-header.light-green {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 10px;
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

.demo-samples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 12px;
  padding: 10px;
  border: 1px solid #e1f0e6;
  border-radius: 10px;
  background: #f8fdf9;
}

.demo-title {
  width: 100%;
  color: #2d5a3d;
  font-size: 13px;
  font-weight: 700;
}

.demo-sample {
  display: flex;
  align-items: center;
  gap: 5px;
  border: 1px solid #c7e5d2;
  border-radius: 8px;
  padding: 4px 7px 4px 4px;
  color: #236641;
  background: #fff;
  font-size: 12px;
}

.demo-sample img {
  width: 30px;
  height: 30px;
  object-fit: cover;
  border-radius: 5px;
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
  color: #24372b;
}

.result-heading { font-size: 17px; font-weight: 600; margin: 0 0 14px; }
.result-empty { color: #62766a; font-size: 14px; padding: 12px 0; }

.result-label {
  border-radius: 10px;
  text-align: left;
  padding: 14px 16px;
  font-size: 18px;
  font-weight: 600;
}

.result-extra {
  margin-top: 6px;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  background: #f4faf7;
  color: #2b7b4f;
}
.result-subtitle { display: flex; align-items: baseline; gap: 8px; margin: 22px 0 10px; font-size: 15px; font-weight: 600; }
.result-subtitle small { color: #718377; font-size: 12px; font-weight: 400; }
.score-row { margin: 10px 0; }
.score-row > div:first-child { display: flex; justify-content: space-between; gap: 12px; font-size: 14px; }
.score-row strong { font-variant-numeric: tabular-nums; color: #1f6f4a; }
.score-track { height: 6px; margin-top: 6px; background: #edf1ec; border-radius: 3px; overflow: hidden; }
.score-track span { display: block; height: 100%; background: #b28a3f; }
.result-advice, .result-record { font-size: 14px; line-height: 1.7; margin: 18px 0 0; color: #486554; }
.result-record { border-top: 1px solid #e1e8e2; padding-top: 12px; }

.label-healthy { background: #daf6e6; color: #1f8a53; }
.label-deficient { background: #ffe8dc; color: #cf5a2a; }
.label-loading { background: #e6f2ff; color: #2d70b7; }
.label-disease { background: #fff2de; color: #c4721e; }
.label-error { background: #ffe8ea; color: #d24f58; }
.verification-form { border-top: 1px solid #dcebe1; margin-top: 16px; padding-top: 14px; }
.verification-title { color: #24563b; font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.verification-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.verification-fields label { display: flex; flex-direction: column; gap: 5px; color: #385946; font-size: 13px; min-width: 0; }
.verification-fields .reference-field { grid-column: 1 / -1; }
.verification-fields select, .verification-fields input { width: 100%; min-width: 0; box-sizing: border-box; border: 1px solid #c7dbcf; border-radius: 6px; padding: 9px; background: #fff; color: #243e2e; font-size: 14px; }
.verification-check { display: flex; align-items: center; gap: 7px; margin: 12px 0; color: #385946; font-size: 13px; }
.btn-confirm { border: 0; border-radius: 6px; padding: 10px 14px; background: #238251; color: #fff; font-size: 13px; font-weight: 600; }
.btn-confirm:disabled { opacity: 0.55; }
.confirmation-message { color: #24563b; font-size: 13px; margin: 9px 0 0; }
@media (min-width: 1024px) {
  .camera-wrap {
    display: grid;
    grid-template-columns: minmax(420px, 560px) minmax(360px, 1fr);
    grid-template-areas: "preview result" "actions result";
    align-items: start;
    justify-content: center;
    column-gap: 32px;
  }
  .camera-box { grid-area: preview; max-width: 560px; }
  .camera-actions { grid-area: actions; max-width: 560px; }
  .result-area {
    grid-area: result;
    max-width: none;
    min-height: 0;
    padding: 16px 0;
  }
}
</style>

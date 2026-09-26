# 烟草病害智能识别系统

基于 YOLOv8 的烟草叶部病害与营养缺乏统一检测系统，覆盖**无人机感知 → 算法识别 → 智能决策 → 精准执行**的全链路。

---

## 一键在线体验（推荐，无需安装任何软件）

点击下方按钮，在浏览器中直接运行完整系统：

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Gong-zheng-zzu/tobacco-disease-detection)

### 操作步骤

1. 点击上方按钮（或在仓库页面点 **Code → Codespaces → Create codespace on master**）
2. 等待环境自动初始化，**约 5-8 分钟**（自动安装依赖、建库、生成演示数据）
   - 终端出现 `服务已启动` 字样即表示就绪
3. 在下方 **PORTS（端口）** 面板中找到 **5173** 端口，点击地球图标打开
4. 使用演示账号登录

| 账号 | 密码 |
|------|------|
| `admin` | `123456` |

### 测试识别功能

仓库已内置测试图片，位于 [`烟草/demo_images/`](烟草/demo_images/)，6 个类别各 3 张，文件名即为正确答案：

| 文件 | 预期识别结果 |
|------|------------|
| `白星病_1~3.jpg` | 白星病 |
| `花叶病_1~3.jpg` | 花叶病 |
| `烟青虫_1~3.jpg` | 烟青虫 |
| `野火病_1~3.jpg` | 野火病 |
| `健康_1~3.jpg` | 健康 |
| `缺钾_1~3.jpg` | 缺钾 |

在首页选择地块后，点击 **从相册选择** 上传任意一张即可看到识别结果与置信度。

---

## 核心技术指标

### 统一检测模型（当前部署版本）

单一 YOLOv8n 模型一次推理识别全部 6 个类别，替代了原先"YOLOv8n 病害检测 + ResNet18 缺素分类"的双模型方案。

| 指标 | 数值 |
|------|------|
| mAP@0.5 | 94.0% |
| 推理速度（GPU, RTX 2050） | 23.9 ms |
| 推理速度（CPU, Codespaces 2 核） | 约 60 ms/张 |
| 模型体积 | 5.99 MB |
| 数据集规模 | 4306 张 / 6 类 |

### 为什么采用单一统一模型

原双模型方案存在三个实测问题：

1. **标签错误**：缺素数据集中标注为"缺磷"的样本实际是缺钾，ResNet18 学到了错误特征
2. **逻辑缺口**：两个模型均无法识别"健康"状态，也无法协调彼此的判断结果
3. **推理耗时**：两次串行推理累计 120 ms

统一为单模型后的实测改进：

| 对比项 | 双模型 | 统一模型 |
|--------|--------|---------|
| 推理耗时 | 120 ms | 23.9 ms（5 倍提升）|
| 缺钾识别 | 误判为缺磷 | 98.8% 准确 |
| 健康状态识别 | 不支持 | 支持 |
| 多目标同时检测 | 不支持 | 支持 |

`demo_images/` 中 18 张图片的 CPU 实测结果为 **18/18 全部识别正确**，其中缺钾 3 张均未出现历史上的白星病误判。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 算法层 | YOLOv8（Ultralytics）、PyTorch |
| 后端 | Django 4.2 + Django REST Framework |
| 前端 | Vue 3 + Vite + ECharts + 高德地图 API |
| 数据库 | SQLite（演示）/ MySQL（生产可选）|
| 边缘部署 | Jetson Nano（TensorRT INT8，规划中）|

## 主要功能模块

- **智能识别**：拍照或上传图片，一次识别 4 种病害 + 健康状态 + 缺钾
- **数据分析**：缺素趋势、病害统计的可视化图表（ECharts）
- **施肥管理**：基于识别结果自动生成追肥建议与施肥记录
- **农药管理**：检测到病害后自动创建对应农药记录
- **设备管理**：传感器、无人机、执行器的状态监控
- **地块管理**：高德地图集成的地块可视化
- **AI 咨询**：基于大模型的农技问答（需配置 API 密钥，见下）

---

## 本地运行（可选）

若需在本地运行而非 Codespaces：

```bash
# 后端
cd 烟草/前后端/drf_test002
pip install -r requirements.txt
python manage.py migrate
python manage.py generate_sample_data   # 生成演示数据
python manage.py runserver 0.0.0.0:8000

# 前端（另开一个终端）
cd 烟草/前后端/tobacco
npm install
npm run dev
```

前端访问 `https://localhost:5173`（本地使用 mkcert 自签证书以支持摄像头功能）。

### AI 咨询功能的密钥配置

AI 咨询模块需要阿里云 DashScope API 密钥。密钥不随仓库分发，需自行配置：

- **本地**：设置环境变量 `DASHSCOPE_API_KEY`
- **Codespaces**：在 GitHub → Settings → Codespaces → Secrets 添加 `DASHSCOPE_API_KEY`

未配置时 AI 咨询会返回提示信息，**其余功能（含病害识别）均不受影响**。

---

## 项目结构

```
烟草/
├── demo_images/              演示用测试图片（6类×3张）
├── 前后端/
│   ├── drf_test002/          Django 后端
│   │   ├── app2/             业务应用（模型、视图、API）
│   │   └── model_weights/    模型权重
│   └── tobacco/              Vue 3 前端
├── unified_tobacco_dataset/  统一 6 类数据集（4306 张）
├── scripts/                  训练与测试脚本
└── docs/                     技术文档
.devcontainer/                Codespaces 环境配置
```

## 说明

本演示环境为便于验收而配置，采用 `DEBUG=True` 且检测接口未启用鉴权，**不适用于生产部署**。生产环境需关闭 DEBUG、配置独立密钥、启用接口认证并切换至 MySQL。

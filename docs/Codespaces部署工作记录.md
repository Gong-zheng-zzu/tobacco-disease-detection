# Codespaces 演示环境部署 - 工作记录

日期：2026-09-26
提交：`0669f80 [Codespaces] 配置一键云端演示环境`
仓库：https://github.com/Gong-zheng-zzu/tobacco-disease-detection

---

## 一、目标与方案选择

**需求**：项目需提交可执行程序，让考官能直接看到并使用系统。

**方案对比**：

| 方案 | 结论 | 原因 |
|------|------|------|
| GitHub Pages | ❌ 不可行 | 只托管静态文件，跑不了 Django + YOLO 推理，部署后是点"识别"就报错的空壳 |
| 打包 exe | ❌ 不可行 | torch + ultralytics + 权重打包后 2-5GB；PyInstaller 打包 torch 极易失败；MySQL 无法打包 |
| 内网穿透 | ⚠️ 可行但有依赖 | 需答辩时本人电脑保持开机 |
| **GitHub Codespaces** | ✅ 采用 | 真正的云端 Linux 容器，能跑完整技术栈，不依赖本人设备 |

**Codespaces 可行的三个前提**（探索后确认）：
1. 数据库**已经是 SQLite**（`settings.py` 中 MySQL 配置已被注释），无需改造
2. 前端**无硬编码后端地址**，全部走相对路径 `/api/*` + Vite proxy，只需暴露 5173 一个端口
3. 生产权重仅 **5.99MB**，远低于 GitHub 单文件 100MB 限制，可直接提交

---

## 二、解除的阻塞项

原仓库有 6 处问题会让考官打开后直接报错。

### 1. 模型权重与测试图片被 gitignore（最严重）

**问题**：根 `.gitignore` 排除 `*.pt` / `*.pth` / `*.jpg` / `*.png`，考官 clone 后没有模型文件，检测接口必然返回 503。

**处理**：
- 两个 `.gitignore` 加白名单例外，放行 `yolo_unified_6class_best.pt`
- 新建 `烟草/demo_images/`，从测试集挑选 6 类各 3 张纯净样本（仅含单一类别标注），按中文类别命名便于考官对照

**文件**：`.gitignore`、`烟草/.gitignore`、`烟草/demo_images/`（18 张）

### 2. ALLOWED_HOSTS 不含 Codespaces 域名

**问题**：原值是硬编码的局域网 IP 清单，转发域名访问会直接 400 DisallowedHost。

**处理**：追加 `.app.github.dev`、`.github.dev`、`.preview.app.github.dev`；补充 `CSRF_TRUSTED_ORIGINS`（Django 4.2 跨域 POST 需要，检测端点因 `authentication_classes=[]` 不受影响，但 admin 登录需要）。

**文件**：`烟草/前后端/drf_test002/drf_test002/settings.py`

### 3. torch 无版本约束

**问题**：`pip install torch` 会拉最新 CUDA 版 wheel（2-3GB），无 GPU 的容器纯属浪费且可能超时或撑爆磁盘。

**处理**：加 `--extra-index-url` 指向 CPU 索引，锁定 `torch==2.3.1` / `torchvision==0.18.1`（约 200MB）；`ultralytics` 锁定上界 `<8.4.0` 防止版本漂移导致权重反序列化失败；`numpy<2.0`。

**文件**：`烟草/前后端/drf_test002/requirements.txt`

### 4. mysqlclient 依赖多余且易失败

**问题**：`mysqlclient>=2.2.0` 需系统级 `libmysqlclient-dev` 才能编译，是容器环境常见失败点，而项目实际用 SQLite，这个依赖根本用不上。

**处理**：移除，并在文件中注明原因。

### 5. Vite 6 拒绝转发域名

**问题**：Vite 6 默认拒绝非白名单 Host，Codespaces 转发域名会被拒，前端打不开。另外 `mkcert` 自签证书在 Codespaces 里是多余的（转发层已提供 HTTPS），反而可能引起握手失败。

**处理**：新增 `server.allowedHosts` 放行转发域名；按 `CODESPACES` 环境变量判断，容器内走 http 并跳过 mkcert 插件。摄像头依赖的 secure context 由 GitHub 转发层的 HTTPS 满足。

**文件**：`烟草/前后端/tobacco/vite.config.js`

### 6. 无自动化启动配置

**处理**：新建 `.devcontainer/` 三个文件。

- `devcontainer.json` — Python 3.11 + Node 20；`forwardPorts: [5173, 8000]`，5173 设为 `public` 并自动打开预览
- `setup.sh`（容器创建时一次性）— 装 Python/前端依赖 → 校验权重（缺失时从 `烟草/models/` 回退复制）→ migrate → 生成演示数据
- `start.sh`（每次连接容器）— 后台起 Django 8000 + Vite 5173，带端口占用检测避免重连时起两份，打印访问提示

---

## 三、修复的 Bug

### 1. 演示数据只生成 1 个地块

**位置**：`app2/management/commands/generate_sample_data.py:25`

原代码 `get_or_create(user=user, defaults={'name': name, 'area': area})` 的查找条件只有 `user`，循环 5 次后 4 次都匹配到第一条记录。修正为把 `name` 纳入查找条件。

**验证**：全新空库实测生成 **5 个地块**、50 条缺素记录、25 个设备（修复前只有 1 个地块）。

### 2. 硬编码 API key 会随公开仓库泄露

**位置**：`app2/views/AIconsult.py:14`

原代码把 DashScope API key 作为 `os.getenv` 的 fallback 值硬编码。改为仅从环境变量读取（`DASHSCOPE_API_KEY`），不留 fallback；key 缺失时返回友好提示而非 500 报错，其余功能不受影响。

### 3. Shell 脚本行尾风险（预防性修复）

Git 默认会把 `*.sh` 转成 CRLF，而 Linux 容器执行带 CRLF 的 bash 脚本会报 `$'\r': command not found`，直接导致环境初始化失败。

新建 `.gitattributes` 强制 `*.sh` 与 `.devcontainer/**` 使用 LF，并将模型权重、图片标记为 binary 禁止任何转换。

**验证**：`git ls-files --eol` 显示 `i/lf w/lf`，确认仓库内与工作区均为 LF。

### 4. README 性能指标写错（本次发现并修正）

最初 README 写 mAP@0.5 = 94.0%，核对训练记录后发现真实值是 **96.18%**。已修正，详见下节。

---

## 四、实测验证结果

所有关键路径都实际运行过，不是仅检查配置文件。

| 验证项 | 结果 |
|--------|------|
| 18 张示例图 CPU 推理 | **18/18 全部识别正确**，6 类无误判 |
| 缺钾专项（历史 bug 回归检查） | 3/3 正确识别为缺钾，**无白星病误判** |
| 检测 API 端到端 | **4/4 通过**（缺钾/白星病/健康/烟青虫）|
| CPU 推理耗时 | 单张 84-160ms（首张 6.4s 含模型加载）|
| 演示数据生成（空库） | 5 地块 + 50 缺素记录 + 25 设备 |
| `manage.py check` | no issues |
| shell 脚本 `bash -n` | 两个脚本语法均通过 |
| `devcontainer.json` | JSON 解析通过，5173 visibility=public |
| 远程仓库文件核对 | 7 个关键文件全部存在 |

### 已部署模型的真实性能

从训练记录 `runs/yolo_training/unified_6class_20260912_104707/results.csv` 提取（已用 MD5 核对该训练产物与部署权重为同一文件）：

| 指标 | 数值 |
|------|------|
| mAP@0.5 | **96.18%** |
| mAP@0.5-0.95 | 86.79% |
| Precision | 95.17% |
| Recall | 92.95% |

---

## 五、待处理问题

### 🔴 需要你手动操作

**1. 实测一次 Codespaces 启动**（最重要）

我无法代为创建 Codespace（需 GitHub 账号授权）。建议先自己走完整流程，确认无误再给考官链接：

```
https://codespaces.new/Gong-zheng-zzu/tobacco-disease-detection
```

重点观察两处：
- `setup.sh` 安装 torch 是否超时（2 核机器上约 200MB 下载）
- PORTS 面板中 5173 端口的 visibility 是否为 Public

失败时日志在容器内 `/tmp/tobacco-logs/{django,vite}.log`。

**2. 确认 Codespaces 额度可用**

个人账号每月 120 核小时免费（2 核机器约 60 小时）。组织仓库需管理员在 Settings 中开启。

**3. 重新生成 DashScope API key**

原 key 已提交进 git 历史，改代码无法撤回已泄露的部分。建议：
- 到 DashScope 控制台重新生成，旧 key 作废
- 新 key 加到 GitHub → Settings → Codespaces → Secrets，名称 `DASHSCOPE_API_KEY`
- 不配也可以——AI 咨询会返回提示，病害识别等功能不受影响

### 🟡 演示环境的已知局限

**安全配置不适用于生产**：`DEBUG=True`、硬编码 `SECRET_KEY`、检测接口无鉴权（其中 `UnifiedDetectionView` 会写数据库）。公开转发域名下任何拿到链接的人都能调用。演示场景可接受，建议**答辩结束后停掉 Codespace**。

**高德地图 key 在前端源码中**（`Strategy.vue:308`）。Web 端 key 本身设计为公开可见，但应在高德控制台配置域名白名单限制滥用。该 key 也已在 git 历史中。

**CPU 推理比 GPU 慢**：84-160ms vs 23.9ms。演示体验仍流畅，无需处理。

### 🟢 算法层的遗留问题（与本次部署无关）

这些是 Phase 6 算法优化的未完成项：

**1. YOLOv8m 训练失败，性能反而下降**

已训练完成但不如基线，**未部署**：

| 指标 | YOLOv8n（已部署）| YOLOv8m | 变化 |
|------|----------------|---------|------|
| mAP@0.5 | 96.18% | 84.3% | **-11.9%** |
| 烟青虫 mAP@0.5-0.95 | 59.4% | 48.4% | **-11.0%** |

根因分析：`batch=4`（RTX 2050 显存 4GB 限制）对 25.9M 参数的模型太小，BatchNorm 统计不准、梯度噪声大。基线 YOLOv8n 用的是 `batch=16`。训练曲线显示 Epoch 90-100 在 84% 附近停滞无法突破。

后续选项：换 8GB+ 显存 GPU 用 batch=16 重训 / 改用 YOLOv8s（11.2M 参数，batch=8 可行）/ 放弃通用提升转做专项优化。

**2. 烟青虫小目标检测仍是瓶颈**

已部署模型该类 mAP@0.5-0.95 = 59.4%，明显低于其他类别（0.8+）。虫体占叶片不足 5%，640×640 输入下 32 倍下采样后小目标特征丢失。

已备脚本未执行：`scripts/train_yolov8_p6_small_objects.py`（4 检测头 + 1280 分辨率）。

**3. 白星病与花叶病混淆**

白星病准确率 75%，20% 误判为花叶病。会导致错误用药（白星病需铜制剂，花叶病需病毒防治）。

已备脚本未执行：`scripts/train_disease_confusion_fix.py`（困难样本挖掘 + 3 倍权重重采样）。

**4. 数据集不平衡**

健康类仅 24 张（0.56%），烟青虫 1653 张（38.4%），比例 69:1。健康类 mAP 虽达 99.5%，但仅基于 24 张特定图像，泛化能力存疑。

---

## 六、本次改动文件清单

**新增**

```
.devcontainer/devcontainer.json     Codespaces 容器定义
.devcontainer/setup.sh              环境初始化（装依赖、建库、灌数据）
.devcontainer/start.sh              服务启动（Django + Vite）
.gitattributes                      强制 *.sh 为 LF 行尾
README.md                           考官入口文档
docs/开发笔记.md                     原 readme 内容（rebase 时保留）
烟草/demo_images/                    18 张示例图（6类×3）
烟草/前后端/drf_test002/model_weights/yolo_unified_6class_best.pt
```

**修改**

```
.gitignore                          白名单放行权重与示例图
烟草/.gitignore                      同上
烟草/前后端/drf_test002/drf_test002/settings.py        ALLOWED_HOSTS + CSRF
烟草/前后端/drf_test002/requirements.txt              torch CPU 版，移除 mysqlclient
烟草/前后端/drf_test002/app2/views/AIconsult.py       移除硬编码 key
烟草/前后端/drf_test002/app2/management/commands/generate_sample_data.py   修地块 bug
烟草/前后端/tobacco/vite.config.js                    allowedHosts + 条件禁用 mkcert
```

共 31 个文件，408 行新增。

注：rebase 时远程有一个网页端创建的 `README.md`（内容为原开发笔记），与本次新建的 README 冲突。已将其保留为 `docs/开发笔记.md`，README 使用面向考官的新版本，内容未丢失。

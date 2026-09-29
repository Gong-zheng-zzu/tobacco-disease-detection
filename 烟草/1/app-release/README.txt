HBuilderX 云打包说明

1. 直接在 HBuilderX 打开本目录: app-release
2. 右键项目 -> 发行 -> 原生App-云打包
3. Android 选择测试证书或你的正式证书
4. 打包即可

说明:
- 当前入口: dist/index.html
- 当前后端地址来自前端构建时的 VITE_API_HOST
- 后端以 烟草/前后端/drf_test002 为准，必须部署统一检测接口及 yolo_unified_6class_best.pt
- 公网 HTTPS 地址 https://8.152.4.105 已通过登录接口验证，打包后仍需真机测试
- 注册需要邮箱验证码。生产后端通过 /etc/tobacco.env 配置 DJANGO_EMAIL_USER 和
  DJANGO_EMAIL_PASSWORD（QQ 邮箱 SMTP 授权码）；授权码不可写入源码或 APK。
- 本地调试 APK 版本为 1.0.12，文件为 叶擎慧航-debug-1.0.12.apk。
- 若后端 IP 变化，请到 app/true/tobacco/.env.production 修改 VITE_API_HOST，
  重新执行 npm run build 后，把新的 dist 同步到本目录再打包。


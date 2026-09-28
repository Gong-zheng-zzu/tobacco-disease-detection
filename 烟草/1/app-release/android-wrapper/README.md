# 叶擎慧航 Android 本地 APK 壳

这是 `app-release/dist` 的独立 Android WebView 包装工程，适用于无法使用 HBuilderX 云打包时生成测试 APK。业务页面和 API 地址均来自内置生产 `dist`，后端为 `https://8.152.4.105`。

## 构建

需要 JDK 17、Android SDK 35 和 Gradle 8.13：

```powershell
$env:JAVA_HOME='D:\android-build\jdk-17.0.20.1+1'
& 'D:\android-build\gradle-8.13\bin\gradle.bat' --no-daemon assembleDebug
```

产物位于 `app/build/outputs/apk/debug/app-debug.apk`。这是 debug 签名 APK，仅用于评委测试和现场演示；正式发布应使用 HBuilderX 云打包或正式签名证书。

此包装工程通过 `WebViewAssetLoader` 的本地 HTTPS 来源加载 `assets/dist/index.html`。不要改回 `file:///android_asset/`，否则 Vite ES module 在部分 Android WebView 中会被拦截并出现白屏。调试时用 `adb logcat -s YQHH-WebView:D chromium:E` 查看前端错误。

构建前如前端有更新，需要将最新 `app-release/dist` 同步至 `app/src/main/assets/dist`。

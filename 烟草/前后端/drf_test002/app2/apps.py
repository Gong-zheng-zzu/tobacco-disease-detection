import os
from django.apps import AppConfig


class App2Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app2"


# 信号文件 signal.py 通过 app 的 ready 方法加载
    def ready(self):
        import app2.signals  # noqa
        # 预加载缺素识别模型，避免首次请求等待（仅在实际服务进程内加载）
        if os.environ.get("RUN_MAIN") == "true":
            try:
                from app2.views.nutrient_df import _preload_nutrient_model
                _preload_nutrient_model()
            except Exception:  # 模型可选，失败不影响其他功能
                pass
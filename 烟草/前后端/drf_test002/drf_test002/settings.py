import os
from pathlib import Path
from corsheaders.defaults import default_headers



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', "django-insecure-s-6luf8(=*a)_uv^6y$43_gw*b$a@r-_3g9o(&0ny%muzhk_=@")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'

# Gunicorn only listens on loopback; Nginx supplies this header for HTTPS traffic.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

CORS_ALLOW_ALL_ORIGINS = True

ALLOWED_HOSTS = [
    '192.168.170.30', 'localhost', '127.0.0.1', '192.168.170.76', '47.98.18.59',
    # GitHub Codespaces 端口转发域名
    '.app.github.dev',
    '.github.dev',
    '.preview.app.github.dev',
    '10.193.148.242',
    '192.168.186.1',
    '192.168.67.1',
]
ALLOWED_HOSTS += [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]

# Django 4.2 对跨域 POST 需要显式信任来源。
# 统一检测端点因 authentication_classes=[] 不触发 CSRF，但 admin 登录需要。
CSRF_TRUSTED_ORIGINS = [
    'https://8.152.4.105',
    'https://*.app.github.dev',
    'https://*.github.dev',
]

# Application definition
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 允许的请求来源（根据前端地址调整）
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # UniApp H5开发地址
    "http://127.0.0.1:5173",

    "http://192.168.242.1:5173", # 手机测试时的前端地址
    "http://192.168.242.1:5173",
    "http://192.168.170.212:5173"

]

# 允许的请求方法（需包含 PUT/PATCH 以支持设备状态切换、修改等）
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

# 允许的请求头
CORS_ALLOW_HEADERS = (*default_headers, 'x-active-role', 'x-user-token')

# 允许携带Cookie（如需）
CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'app2.apps.App2Config',
    'corsheaders',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "drf_test002.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates']
        ,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "drf_test002.wsgi.application"


# Database - SQLite for testing (MySQL config commented out)
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# MySQL配置（需要时取消注释并启动MySQL服务）
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'test_db',
#         'USER': 'root',
#         'PASSWORD': '123456',
#         'HOST': 'localhost',
#         'PORT': '3306',
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         },
#     }
# }





# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

REST_FRAMEWORK = {
    'NUM_PROXIES': 1,
    'DEFAULT_AUTHENTICATION_CLASSES': ['app2.security.LegacyTokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['app2.security.BusinessPermission'],
    'DEFAULT_THROTTLE_RATES': {
        'register': '5/hour',
        'login': '10/minute',
        'captcha': '30/minute',
        'email_code': '5/hour',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'tobacco-auth-cache',
    },
}

EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('DJANGO_EMAIL_HOST', 'smtp.qq.com')
EMAIL_PORT = int(os.getenv('DJANGO_EMAIL_PORT', '465'))
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = os.getenv('DJANGO_EMAIL_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('DJANGO_EMAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 10


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# 推理模型权重（位于项目根目录 model_weights/）
# 可通过环境变量覆盖路径，便于不同部署环境
# ---------------------------------------------------------------------------
MODEL_WEIGHTS_DIR = BASE_DIR / "model_weights"
NUTRIENT_DEFICIENCY_MODEL_PATH = str(MODEL_WEIGHTS_DIR / "model_resnet18.pth")
DISEASE_MODEL_PATH = str(MODEL_WEIGHTS_DIR / "yolov8n_best.pt")
UNIFIED_MODEL_PATH = str(MODEL_WEIGHTS_DIR / "yolo_unified_6class_best.pt")

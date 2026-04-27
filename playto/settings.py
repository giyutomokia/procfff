import os
import dj_database_url

# 🔐 Security
SECRET_KEY = os.environ.get("SECRET_KEY", "test-key")

DEBUG = False

ALLOWED_HOSTS = ["*"]


# 📦 Apps
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    'rest_framework',
    'payouts.apps.PayoutsConfig',  # ✅ required for auto-seed
]


# ⚙️ Middleware
MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]


# 🌐 URLs
ROOT_URLCONF = 'playto.urls'


# 🗄️ Database (Render + Local)
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3'
    )
}


# 🔢 Default ID
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 📡 DRF Config
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}

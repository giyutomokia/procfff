INSTALLED_APPS = [
    'rest_framework',
    'payouts',   # ✅ MUST BE HERE
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
DEBUG = False

ALLOWED_HOSTS = []
import os

from pathlib import Path
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from decouple import config

# OneID uchun sozlamalar
#ONEID_CLIENT_ID = config('ONEID_CLIENT_ID')
#ONEID_CLIENT_SECRET = config('ONEID_CLIENT_SECRET')
#ONEID_REDIRECT_URI = config('ONEID_REDIRECT_URI')
#ONEID_AUTH_URL = 'https://sso.egov.uz/sso/oauth/Authorization.do'  # Auth Endpoint
#ONEID_TOKEN_URL = 'https://sso.egov.uz/sso/oauth/Authorization.do'  # Token Endpoint
#ONEID_REDIRECT_URI = 'https://malakaviy.nuu.uz/applications/'  # Callback URL (loyihangizga moslang)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'SECRET_KEY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['malakaviy.nuu.uz', 'localhost']



#foydalanuvchini chiqarib yuborish
# Sessiya muddatini 10 daqiqaga o'rnatish (sekundlarda)
SESSION_COOKIE_AGE = 2000

# Sessiya avtomatik uzaytirilmasligi uchun
SESSION_SAVE_EVERY_REQUEST = True

# Brauzerni yopganda sessiya tugashini faollashtirish
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'miuz',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',  
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # allauth middleware
    'allauth.account.middleware.AccountMiddleware',  
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

INSTALLED_APPS += ['crispy_forms']
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = False  # Mahalliy vaqt zonasida saqlash uchun

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


STATICFILES_DIRS = [
    BASE_DIR / "config/static/"
]
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTHENTICATION_BACKENDS = (
    'allauth.account.auth_backends.AuthenticationBackend',
)

SITE_ID = 1

# Kirishdan so'ng foydalanuvchi qayerga o'tishini belgilash
# settings.py
# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # Bir yil
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPSni majburiy qilish
SECURE_SSL_REDIRECT = True

# Cookie xavfsizligi
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGIN_REDIRECT_URL = 'applications/'  # Tizimga kirgandan keyin yo'naltirish
LOGOUT_REDIRECT_URL = '/'  # Logoutdan keyin yo'naltirish
LOGIN_URL = '/'  # Login bo'lmagan holatda yo'naltirish

import os

from pathlib import Path
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from decouple import config

SECRET_KEY = config('SECRET_KEY')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = ['mi.nuu.uz', 'malakaviy.nuu.uz', '127.0.0.1']


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
    'allauth.socialaccount.providers.oauth2',
    ]


# OneID uchun sozlamalar
ONEID_CLIENT_ID = config('ONEID_CLIENT_ID')
ONEID_CLIENT_SECRET = config('ONEID_CLIENT_SECRET')
ONEID_AUTH_URL = 'https://sso.egov.uz/sso/oauth/Authorization.do'
ONEID_TOKEN_URL = 'https://sso.egov.uz/sso/oauth/Authorization.do'
ONEID_USER_INFO_URL = 'https://sso.egov.uz/sso/oauth/Authorization.do'
# settings.py
ONEID_REDIRECT_URI = 'https://mi.nuu.uz/callback/'  # URL oxirida "/" borligiga ishonch hosil qiling


SITE_ID = 1
OAUTH2_PROVIDER = {
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
    },

    'CLIENT_ID_GENERATOR_CLASS': 'oauth2_provider.generators.ClientIdGenerator',

}


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
# Django bazaviy kodirovkasi
DEFAULT_CHARSET = 'utf-8'

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


#foydalanuvchini chiqarib yuborish

#SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Sessiya ma'lumotlarini DB da saqlash
#SESSION_COOKIE_AGE = 1200  # 20 daqiqa (sekundlarda)
#SESSION_SAVE_EVERY_REQUEST = True  # Har bir so�rovda sessiya yangilanadi
#SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Brauzerni yopganda sessiya saqlansin
#SESSION_COOKIE_SECURE = True  # HTTPS ishlatilayotgan bo�lsa True
#SESSION_COOKIE_HTTPONLY = True  # JS tomonidan sessiyani o'qishdan himoya
#SESSION_COOKIE_SAMESITE = 'Lax'  # Faqat shu domen uchun cookie yuborish
#CSRF_COOKIE_SECURE = True

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True
USE_L10N = True
USE_TZ = True


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = False  # Mahalliy vaqt zonasida saqlash uchun


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


AUTH_USER_MODEL = 'miuz.CustomUser'



STATICFILES_DIRS = [
    BASE_DIR / "config/static/"
]
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Kirishdan so'ng foydalanuvchi qayerga o'tishini belgilash
# settings.py
# HSTS (HTTP Strict Transport Security)

#SECURE_HSTS_SECONDS = 31536000  # Bir yil
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#SECURE_HSTS_PRELOAD = True
# HTTPSni majburiy qilish
#SECURE_SSL_REDIRECT = True


# Cookie xavfsizligi

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# settings.py
LOGIN_URL = '/'  # Login sahifasi
LOGIN_REDIRECT_URL = '/applications/'  # Autentifikatsiyadan keyin yo'naltirish
LOGOUT_REDIRECT_URL = '/'  # Chiqishdan keyin yo'naltirish

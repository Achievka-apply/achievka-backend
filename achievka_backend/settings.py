from pathlib import Path
from datetime import timedelta

import os
import environ
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env()  # читает .env
from dotenv import load_dotenv
load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
SECRET_KEY ='django-insecure-&j*=9s9c$g(8udy-d769rmbjsqc)e^!6bp+ux-slfog&ay^2d5'
# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = os.environ.get('DJANGO_DEBUG')
DEBUG = True

ALLOWED_HOSTS = [
    "51.20.95.96",    # IP вашего EC2
    "localhost",
    "dev.achievka.com",
    "https://dev.achievka.com",


]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # THIRD-PARTY APPS
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    'dj_rest_auth',
    'dj_rest_auth.registration',
    'rest_framework_simplejwt.token_blacklist',
    'drf_yasg',
    'django_filters',

    # OAuth PROVIDERS
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.apple',
    'allauth.socialaccount.providers.microsoft',
    # MY APPS
    'users.apps.UsersConfig',
    'universities',
    'letters',

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]
# Адреса, с которых можно делать защищённые CSRF-запросы при HTTPS
CSRF_TRUSTED_ORIGINS = [
    "https://dev.achievka.com",
]

# (Опционально, но рекомендовано для HTTPS)
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://51.20.95.96",
    "http://localhost:3000",
    "https://dev.achievka.com",

]
SOCIALACCOUNT_ADAPTER = "users.adapters.AutoConnectSocialAccountAdapter"

CORS_ALLOW_CREDENTIALS = True    # разрешаем куки/credentials
# все разрешённые callback’и
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '466267924459-fs938d881mmptootocn43nrp7onfd4lr.apps.googleusercontent.com',
            'secret':  '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',

            'key':       ''
        },
        'SCOPE': ['openid', 'email', 'profile'],
        'AUTH_PARAMS': {'access_type': 'offline'},
    },
    # … другие провайдеры …
    "microsoft": {
        "APPS": [
            {
                "client_id": "46ed08f7-97cd-4fa9-bdfc-eb89449e034",
                "secret": "f84eb9d6-9345-4a37-a15f-62022002f04d",
                "settings": {
                    "tenant": "organizations",  # multi-tenant
                    "login_url": "https://login.microsoftonline.com",
                    "graph_url": "https://graph.microsoft.com",
                }
            }
        ],
        # обязательно указать scope и response_type
        "SCOPE": ["openid", "email", "profile", "offline_access", "User.Read"],
        "AUTH_PARAMS": {"response_type": "code"},
    },
    'facebook': {
        'APP': {
            'client_id': '10081722528562211',
            'secret': '9db3a9a80115d7b64a2f59f560abc83c',
        },
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=6000),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
    # включить ротацию refresh-токенов
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'allauth':               {'handlers': ['console'], 'level': 'DEBUG'},
        'allauth.socialaccount': {'handlers': ['console'], 'level': 'DEBUG'},
    },
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

SITE_ID = 1
# allauth
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'

ACCOUNT_LOGIN_METHODS    = ['email']
ACCOUNT_SIGNUP_FIELDS    = ['email*', 'password1*', 'password2*']

# dj-rest-auth
REST_USE_JWT = True
JWT_AUTH_COOKIE = 'access_token_cookie'
JWT_AUTH_REFRESH_COOKIE = 'refresh_token_cookie'
TOKEN_MODEL = None
REST_AUTH_TOKEN_MODEL = None

AUTH_USER_MODEL = 'users.User'


EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")


# AWS S3
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
ASSISTANT_COMMON_APP_ID = "asst_Leny043v8KKuVaRGUmJj0Q0z"
ASSISTANT_UCAS_ID       = "asst_gkyVDyNrJPsiEHrzlbTWBkWs"
ASSISTANT_MOTIVATION_ID = "asst_ai22qf4n0MTRAzWkhgPnGL7t"
AWS_S3_BUCKET         = os.getenv("AWS_S3_BUCKET")
AWS_REGION            = os.getenv("AWS_REGION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ROOT_URLCONF = 'achievka_backend.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'achievka_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

MIGRATION_MODULES = {
    'account': None,
}



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'achievka_db',
        'USER': 'achievka',
        'PASSWORD': 'pg_achievka',
        'HOST': 'db',
        'PORT': '5432'
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL  = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

import os
import environ


from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-a2(7q3ve^r^(_n0*%@u6p+w4y)65gg@=mmx)n8g81oxhl@6gh)"

# SECURITY WARNING: don't run with debug turned on in production!
if os.environ.get("GITHUB_ACTIONS") == "true":
    DEBUG = env.bool("DJANGO_DEBUG", default=False)
else:
    DEBUG = env.bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = [
    "*",
    "pomjuice-env.eba-kr2ryzsj.us-west-1.elasticbeanstalk.com",
    "pomjuice-prod.eba-kr2ryzsj.us-west-1.elasticbeanstalk.com",
    "pomjuice-production-env.eba-kr2ryzsj.us-west-1.elasticbeanstalk.com",
    ]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_yasg",
    "cities_light",
    "django_filters",
    "phonenumber_field",
    "import_export",
    "users",
    "investors",
    "locations",
    "reviews",
    "startups",
    "storages",
    "tracks",
    "payment",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware"
]

ROOT_URLCONF = "pjbackend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "pjbackend.wsgi.application"


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'users.permissions.IsRegistered',
    ],
}

AUTH_USER_MODEL = "users.CustomUser"

REGEX_STRING = r"^[ a-zA-ZÀ-ÿ\u00f1\u00d1\'-.]*$"
SIGNUP_EXPIRATION_SECONDS = 86400

MAX_LENGTH_CONFIG = {
    'names': 150,
    'description': 1000,
    'email': 254,
    'url': 500,
    'industry':150,
    'location': 100,
    'password':128,
    'relationship':150,
    'business_model':20,
    'tag_line': 1000,
    'verification_code':4
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'DEBUG',
    },
}

if not env.bool("BUILD_PIPELINE"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_DATABASE"),
            "USER": env("DB_USERNAME"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT"),
            "OPTIONS": {
                "options": "-c search_path=public" 
            }
        }
    }
else:
   DATABASES = {
        'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        }
     }


if not env.bool("BUILD_PIPELINE"):
   CACHE_ENDPOINT = env('CACHE_ENDPOINT')
   CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': CACHE_ENDPOINT,  
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                "TIMEOUT": 300,  
                "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
                "IGNORE_EXCEPTIONS": True,
            }
        }
    }


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
         minutes=env.int(
            "ACCESS_TOKEN_LIFETIME",
            default=120,
        )
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("REFRESH_TOKEN_LIFETIME", default=1)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(days=1),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=120),
}

if env.bool("USE_S3"):
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_CUSTOM_DOMAIN = "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }

    AWS_STATIC_LOCATION = "static"
    STATICFILES_STORAGE = "pjbackend.storage_backends.StaticStorage"

    STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_STATIC_LOCATION)

    AWS_PUBLIC_MEDIA_LOCATION = "media/public"
    DEFAULT_FILE_STORAGE = "pjbackend.storage_backends.PublicMediaStorage"

    AWS_PRIVATE_MEDIA_LOCATION = "media/private"
    PRIVATE_FILE_STORAGE = "pjbackend.storage_backends.PrivateMediaStorage"

else:
    AWS_STATIC_LOCATION = "static"

    AWS_PUBLIC_MEDIA_LOCATION = "media/public"
    DEFAULT_FILE_STORAGE = "pjbackend.storage_backends.PublicMediaStorage"

    AWS_PRIVATE_MEDIA_LOCATION = "media/private"
    PRIVATE_FILE_STORAGE = "pjbackend.storage_backends.PrivateMediaStorage"
    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "static")
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")


SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }
    },
    'USE_SESSION_AUTH': False,
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True


if not env.bool("BUILD_PIPELINE"):
    CSRF_TRUSTED_ORIGINS = [
        'https://frontend.pomjuice.app',
        'https://backend.pomjuice.app',
        'http://portal.pomjuice.app'
        ]
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://localhost:3000',
        'https://frontend.pomjuice.app',
        'https://backend.pomjuice.app',
        'http://portal.pomjuice.app'
        ]


CORS_ALLOW_HEADERS = [
    "h2pky",
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-device-id",
    "HTTP_HOST",
    "HTTP_REFRESH",
    "HTTP_X_DEVICE_ID",
    "phonetime",
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

CORS_EXPOSE_HEADERS = ['Set-Cookie']


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = 'America/Los_Angeles'

USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.CustomUser"

TEST_RUNNER = "pytest_runner.runner.DiscoverRunner"

SENDGRID_API_KEY = env("SENDGRID_API_KEY")
SENDGRID_EMAIL= env("SENDGRID_EMAIL")
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"  # this is exactly the value 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True

if env.bool("USE_MIXPANEL"):
    MIXPANEL_API_TOKEN=env("MIXPANEL_API_TOKEN")
    MIXPANEL_API_SECRET=env("MIXPANEL_API_SECRET") 
else:
    MIXPANEL_API_TOKEN = None
    MIXPANEL_API_SECRET = None
    
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER')

CITIES_LIGHT_TRANSLATION_LANGUAGES = ['en']
CITIES_LIGHT_INCLUDE_COUNTRIES = ['US', 'CA', 'GB', 'MX']
CITIES_LIGHT_INCLUDE_CITY_TYPES = ['PPL', 'PPLA', 'PPLA2', 'PPLA3', 'PPLA4', 'PPLC', 'PPLF', 'PPLG', 'PPLL', 'PPLR', 'PPLS', 'STLMT',]
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY")
DJSTRIPE_WEBHOOK_SECRET = env("DJSTRIPE_WEBHOOK_SECRET")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_LIVE_MODE = False
MAIN_DOMAIN= env("MAIN_DOMAIN")
PRO_MONTHLY_ID=env("PRO_MONTHLY_ID")
PRO_ANNUAL_ID=env("PRO_ANNUAL_ID")
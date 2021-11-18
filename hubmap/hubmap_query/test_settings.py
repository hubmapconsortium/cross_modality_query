"""
Settings for testing under Travis CI. Notably, connect to a local database
instead of one provided by `docker-compose`.
"""

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "",
    },
}

MONGO_HOSTNAME = "mongo"

# /!!! for development, overridden in `production_settings.py` by Docker container build

MONGO_USERNAME = "root"
MONGO_PASSWORD = "rootpassword"
MONGO_PORT = "27017"
MONGO_DB_NAME = "token_store"
MONGO_COLLECTION_NAME = "pickles_and_hashes"
TOKEN_EXPIRATION_TIME = 14400  # 4 hours in seconds

MONGO_HOST_AND_PORT = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOSTNAME}:{MONGO_PORT}/"

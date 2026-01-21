from pydantic import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    DB_TYPE: str = "FIRESTORE"
    CHACHE_TYPE: str = "REDIS"
    MUSIC_PROVIDER: str = "SPOTIFY"

    SPOTIFY_ID: str
    SPOTIFY_SECRET: str

    FIRESTORE_KEY_FILE: str

    REDIS_HOST: str
    REDIS_PORT: int

    REDIS_COLLECTION = "sessions/{0}/{1}"
    FIRESTORE_COLLECTION = "sessions/{0}"

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
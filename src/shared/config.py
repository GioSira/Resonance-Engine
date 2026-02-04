from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    DB_TYPE: str
    CACHE_TYPE: str
    MUSIC_PROVIDER: str

    SPOTIFY_ID: str
    SPOTIFY_SECRET: str

    FIRESTORE_KEY_FILE: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USER: str
    REDIS_PASSWORD: str

    FIRESTORE_COLLECTION: str 

    LOG_FOLDER: str
    LOG_LEVEL: str

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
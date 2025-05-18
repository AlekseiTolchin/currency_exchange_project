from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    JWT_SECRET_KEY: str = 'default_secret_key'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 5
    CURRENCY_API_KEY: str
    CURRENCY_API_URL: str

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()

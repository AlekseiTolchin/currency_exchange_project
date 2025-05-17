from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CURRENCY_API_KEY: str
    CURRENCY_API_URL: str

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()

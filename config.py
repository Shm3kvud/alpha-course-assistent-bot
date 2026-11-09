from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BOT_TOKEN: str
    GIGACHAT_CREDENTIALS: str        
    GIGACHAT_MODEL: str = "GigaChat"
    POSTGRES_URL: str               

settings = Settings()
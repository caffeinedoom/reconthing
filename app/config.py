# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_NAME: str
    DB_PORT: str = "5432"
    DISCORD_BOT_TOKEN: str
    API_HOST: str = "localhost"
    API_PORT: str = "8000"

    @property
    def DATABASE_URL(self) -> AnyUrl:
        return AnyUrl.build(
            scheme="postgresql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=int(self.DB_PORT),  
            path=f"{self.DB_NAME}",
        )
    
    @property
    def API_URL(self) -> str:
        return f"http://{self.API_HOST}:{self.API_PORT}"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
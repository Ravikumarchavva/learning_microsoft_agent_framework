from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra='allow'
    )

if __name__ == "__main__":
    settings = Settings()
    print("Loaded settings from .env:")
    print(ROOT_DIR)
    print(settings.model_dump())
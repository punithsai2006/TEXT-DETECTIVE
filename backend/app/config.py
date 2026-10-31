from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LLM_PROVIDER: str = "mock"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = ""
    DEMO_MODE: bool = True
    STORAGE_DIR: str = "storage"
    DATA_DIR: str = "data"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Base workspace directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @property
    def storage_path(self) -> Path:
        p = self.BASE_DIR / self.STORAGE_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def data_path(self) -> Path:
        p = self.BASE_DIR / self.DATA_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

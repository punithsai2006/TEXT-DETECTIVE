from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LLM_PROVIDER: str = "mock"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = ""
    DEMO_MODE: bool = True
    SPACY_MODEL: str = ""
    USE_FAISS: bool = False
    ALLOW_MODEL_DOWNLOADS: bool = False
    SCORE_METHOD_VERSION: str = "evidence-support-v3.0"
    SCORE_WEIGHTS: dict[str, float] = {"support": 4, "conflict": -4, "temporal": 1,
                                       "relationships": 1, "coverage": 2, "assumptions": -1}
    MODEL_ASSISTED_ANALYSIS: bool = False
    ANALYSIS_MAX_MODEL_CALLS: int = 24
    ANALYSIS_TIMEOUT_SECONDS: int = 180
    COMPARISON_BATCH_SIZE: int = 40
    MAX_CASE_CANDIDATES: int = 10000
    GRAPH_MAX_HOPS: int = 2
    GRAPH_MAX_NODES: int = 80
    EVIDENCE_CONTEXT_LIMIT: int = 24
    AGENT_MAX_TOOL_CALLS: int = 30
    AGENT_MAX_LLM_CALLS: int = 12
    AGENT_TIMEOUT_SECONDS: int = 180
    STRUCTURED_MAX_ATTEMPTS: int = 2
    API_ACCESS_TOKEN: str = ""
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

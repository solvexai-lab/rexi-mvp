from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "REXI API"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://rexi:rexi_pass@localhost:5432/rexi_db"
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_recycle: int = 300
    db_pool_timeout: int = 30
    db_connect_timeout: int = 10
    db_command_timeout: int = 30
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = "rexi_neo4j_2025"
    openai_api_key: str = ""
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "rexi_minio"
    minio_secret_key: str = "rexi_minio_secret"
    minio_bucket: str = "rexi-contracts"
    upload_dir: str = "./uploads"
    secret_key: str = "rexi-super-secret-change-me-in-production"

    # Langfuse observability
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"
    langfuse_enabled: bool = False

@lru_cache()
def get_settings():
    return Settings()

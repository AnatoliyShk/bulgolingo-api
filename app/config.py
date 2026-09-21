from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # webhook_host: str = Field(..., env="WEBHOOK_HOST")
    # webhook_path: str = Field(..., env="WEBHOOK_PATH")
    # webhook_secret_token: str = Field(..., env="WEBHOOK_SECRET_TOKEN")
    bot_token: str = Field(..., env="BOT_TOKEN")
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    database_url: str = Field(..., env="DATABASE_URL")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(60, env="JWT_EXPIRE_MINUTES")
    gemini_model: str = Field("gemini-2.5-flash", env="GEMINI_MODEL")
    gemini_embed_model: str = Field("gemini-embedding-001", env="GEMINI_EMBED_MODEL")
    gemini_embed_dim: int = Field(768, env="GEMINI_EMBED_DIM")

    # @property
    # def webhook_url(self) -> str:
    #     return f"{self.webhook_host}{self.webhook_path}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
# from pydantic import Field
# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     # webhook_host: str = Field(..., env="WEBHOOK_HOST")
#     # webhook_path: str = Field(..., env="WEBHOOK_PATH")
#     # webhook_secret_token: str = Field(..., env="WEBHOOK_SECRET_TOKEN")
#     bot_token: str = Field(..., env="BOT_TOKEN")

#     # @property
#     # def webhook_url(self) -> str:
#     #     return f"{self.webhook_host}{self.webhook_path}"
    
#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"

# settings = Settings()
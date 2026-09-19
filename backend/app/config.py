from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "dev-only-insecure-secret-change-me"
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///./creditlens.db"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days, generous for a demo
    claude_model: str = "claude-sonnet-5"

    class Config:
        env_file = ".env"


settings = Settings()

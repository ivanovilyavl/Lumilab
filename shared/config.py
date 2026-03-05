from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    bot_token: str = ""
    analytics_bot_token: str = ""
    analytics_admin_ids: str = ""
    miniapp_url: str = "http://localhost:5173"
    webhook_url: str = ""
    webhook_secret: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://zapisbot:devpassword@db:5432/zapisbot_dev"
    database_pool_size: int = 10

    # Redis
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # Tribute
    tribute_webhook_secret: str = ""
    tribute_subscription_url: str = ""
    tribute_monthly_price_rub: int = 199

    # Business logic
    trial_days: int = 14
    referral_bonus_days: int = 7
    free_tier_max_services: int = 3

    # Environment
    environment: str = "dev"
    debug: bool = True
    log_level: str = "DEBUG"
    secret_key: str = "change_me"
    allowed_origins: str = "http://localhost:5173"

    @property
    def admin_ids(self) -> list[int]:
        if not self.analytics_admin_ids:
            return []
        return [int(x.strip()) for x in self.analytics_admin_ids.split(",") if x.strip()]

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

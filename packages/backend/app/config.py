"""config.py — env-driven settings.

PHASE1_PATH points at the pricing engine checkout so its flat-layout modules
(db/, models/, calculator/, scanner/) can be put on sys.path without editing or
repackaging it. This repo ships a self-contained open reference engine under
packages/engine/ (the default below); point PHASE1_PATH at your own engine to
swap in real pricing/scanner logic. In Docker this is set to where the image
COPYs the engine package.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# packages/backend/app/config.py -> repo root is 3 parents up from _BACKEND_DIR
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent.parent
# Self-contained reference engine bundled in this repo (swap via PHASE1_PATH).
_DEFAULT_PHASE1 = _REPO_ROOT / "packages" / "engine"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    # Where the Phase 1 engine lives (its db/models/calculator/scanner dirs).
    phase1_path: str = str(_DEFAULT_PHASE1)

    # Persistent Phase 2 SQLite file — must NOT be inside Phase 1's auto-rebuilt data dir.
    oleflip_db_path: str = str(_BACKEND_DIR / "data" / "oleflip.db")

    # Single-user gate for mutating endpoints. Empty string disables the check
    # (dev convenience); set a real value in any deployed environment.
    api_key: str = ""

    # External-service creds (never exposed to the browser).
    apify_api_token: str = ""
    ebay_rapidapi_key: str = ""
    ebay_rapidapi_host: str = ""
    ebay_client_id: str = ""       # official Marketplace Insights API (pending eBay approval)
    ebay_client_secret: str = ""

    # ── LLM providers (agent system) — server-side only, never sent to browser ──
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    openai_api_key: str = ""
    grok_api_key: str = ""

    # Base URLs (env-overridable so a provider can be re-pointed without a code change).
    anthropic_base_url: str = "https://api.anthropic.com"
    deepseek_base_url: str = "https://api.deepseek.com"
    openai_base_url: str = "https://api.openai.com/v1"
    grok_base_url: str = "https://api.x.ai/v1"

    # Per-agent model IDs (drift over time — edit here / in .env, never hardcode in code).
    model_escanner: str = "claude-sonnet-5"
    model_epricer: str = "deepseek-chat"
    model_elistings: str = "deepseek-chat"
    model_einventory: str = "deepseek-chat"
    model_ecustomer: str = "claude-haiku-4-5"
    model_research: str = "claude-sonnet-5"
    model_marketing: str = "claude-haiku-4-5"
    model_auditor: str = "claude-opus-4-8"

    # Voice logging (Tier 2) — cheap/fast provider for transcript → structured items.
    voice_provider: str = "deepseek"
    voice_model: str = "deepseek-chat"

    # Notifications (Tier 3) — all optional; a channel is inert until its creds exist.
    discord_webhook_url: str = ""
    slack_webhook_url: str = ""
    push_vapid_public_key: str = ""
    push_vapid_private_key: str = ""
    push_vapid_email: str = "admin@oleflip.local"

    # Photo uploads (Tier 4).
    upload_dir: str = str(_BACKEND_DIR / "data" / "uploads")
    max_photo_size_mb: int = 10
    max_photos_per_item: int = 15

    # Start the APScheduler background loop at app startup (off in tests).
    agents_scheduler_enabled: bool = True

    # Geocode ITAD supplier addresses on create/update (off in tests — no network).
    geocoding_enabled: bool = True

    # Optional per-agent provider overrides ("" = use the agent's default provider).
    provider_escanner: str = ""
    provider_epricer: str = ""
    provider_elistings: str = ""
    provider_einventory: str = ""
    provider_ecustomer: str = ""
    provider_research: str = ""
    provider_marketing: str = ""
    provider_auditor: str = ""

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def provider_key(self, provider: str) -> str:
        """API key for a provider name, or '' if unset."""
        return {
            "anthropic": self.anthropic_api_key,
            "deepseek": self.deepseek_api_key,
            "openai": self.openai_api_key,
            "grok": self.grok_api_key,
        }.get(provider, "")


settings = Settings()

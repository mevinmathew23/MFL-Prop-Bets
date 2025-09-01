"""Configuration settings for MFL Prop Bets application."""

import json
import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from mfl_prop_bets.models import YearConfig


class PropBetSettings(BaseSettings):
    """Application settings manager."""

    model_config = SettingsConfigDict(env_prefix="MFL_PROP_BET_")

    # Current year to use for calculations
    current_year: str = Field(default="2024", alias="CURRENT_YEAR")

    # File paths
    oauth_file: str = Field(default="./oauth.json", alias="OAUTH_FILE")
    league_info_file: str = Field(
        default="./league_info.json", alias="LEAGUE_INFO_FILE"
    )
    service_account_file: str = Field(
        default="mfl-service-acct.json", alias="SERVICE_ACCOUNT_FILE"
    )

    # Logging configuration
    log_level: str = Field(default="INFO")

    # Google Sheets scope
    google_sheets_scope: list[str] = Field(
        default=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
        alias="GOOGLE_SHEETS_SCOPE",
    )

    @property
    def log_level_int(self) -> int:
        """Convert string log level to logging constant."""
        return getattr(logging, self.log_level.upper(), logging.INFO)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._year_configs: dict[str, YearConfig] | None = None

    @property
    def year_configs(self) -> dict[str, YearConfig]:
        """Load and cache year configurations."""
        if self._year_configs is None:
            self._load_year_configs()
        return self._year_configs

    def _load_year_configs(self) -> None:
        """Load year configurations from league_info.json."""
        league_file_path = Path(self.league_info_file)
        if not league_file_path.exists():
            raise FileNotFoundError(
                f"League info file not found: {self.league_info_file}"
            )

        with open(league_file_path, encoding="utf-8") as f:
            data = json.load(f)

        self._year_configs = {
            year: YearConfig(**config) for year, config in data.items()
        }

    def get_current_year_config(self) -> YearConfig:
        """Get configuration for the current year."""
        if self.current_year not in self.year_configs:
            raise ValueError(f"Configuration for year {self.current_year} not found")
        return self.year_configs[self.current_year]

    def get_year_config(self, year: str) -> YearConfig:
        """Get configuration for a specific year."""
        if year not in self.year_configs:
            raise ValueError(f"Configuration for year {year} not found")
        return self.year_configs[year]

    def load_oauth_credentials(self) -> dict[str, str]:
        """Load OAuth credentials from file."""
        oauth_file_path = Path(self.oauth_file)
        if not oauth_file_path.exists():
            raise FileNotFoundError(f"OAuth file not found: {self.oauth_file}")

        with open(oauth_file_path, encoding="utf-8") as f:
            return json.load(f)

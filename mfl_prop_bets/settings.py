"""Configuration settings for MFL Prop Bets application."""

import json
from pathlib import Path
from models import YearConfig


class Settings:
    """Application settings manager."""
    
    # Current year to use for calculations
    CURRENT_YEAR = "2024"
    
    # File paths
    OAUTH_FILE = "./oauth.json"
    LEAGUE_INFO_FILE = "./league_info.json"
    SERVICE_ACCOUNT_FILE = "mfl-service-acct.json"
    
    # Google Sheets scope
    GOOGLE_SHEETS_SCOPE = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self):
        self._year_configs: dict[str, YearConfig] | None = None
    
    @property
    def year_configs(self) -> dict[str, YearConfig]:
        """Load and cache year configurations."""
        if self._year_configs is None:
            self._load_year_configs()
        return self._year_configs
    
    def _load_year_configs(self) -> None:
        """Load year configurations from league_info.json."""
        league_file_path = Path(self.LEAGUE_INFO_FILE)
        if not league_file_path.exists():
            raise FileNotFoundError(f"League info file not found: {self.LEAGUE_INFO_FILE}")
        
        with open(league_file_path) as f:
            data = json.load(f)
        
        self._year_configs = {
            year: YearConfig(**config)
            for year, config in data.items()
        }
    
    def get_current_year_config(self) -> YearConfig:
        """Get configuration for the current year."""
        if self.CURRENT_YEAR not in self.year_configs:
            raise ValueError(f"Configuration for year {self.CURRENT_YEAR} not found")
        return self.year_configs[self.CURRENT_YEAR]
    
    def get_year_config(self, year: str) -> YearConfig:
        """Get configuration for a specific year."""
        if year not in self.year_configs:
            raise ValueError(f"Configuration for year {year} not found")
        return self.year_configs[year]
    
    def load_oauth_credentials(self) -> dict[str, str]:
        """Load OAuth credentials from file."""
        oauth_file_path = Path(self.OAUTH_FILE)
        if not oauth_file_path.exists():
            raise FileNotFoundError(f"OAuth file not found: {self.OAUTH_FILE}")
        
        with open(oauth_file_path) as f:
            return json.load(f)



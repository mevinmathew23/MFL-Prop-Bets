"""Improved Yahoo OAuth client with better logging and error handling."""

import json
import logging
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel


class OAuthConfig(BaseModel):
    """OAuth configuration model."""

    access_token: str | None = None
    consumer_key: str
    consumer_secret: str
    refresh_token: str | None = None
    token_time: float | None = None
    token_type: str = "bearer"
    guid: str | None = None


class YahooOAuthError(Exception):
    """Custom exception for Yahoo OAuth errors."""


class YahooOAuth:
    """
    Improved Yahoo OAuth 2.0 client with better logging and error handling.

    This client handles OAuth 2.0 flow for Yahoo Fantasy Sports API access,
    with proper token management, refresh capabilities, and configurable logging.
    """

    def __init__(
        self,
        config_file: str | Path,
        logger: logging.Logger | None = None,
        log_level: int = logging.WARNING,
    ):
        """
        Initialize Yahoo OAuth client.

        Args:
            config_file: Path to OAuth configuration JSON file
            logger: Optional custom logger instance
            log_level: Logging level (default: WARNING to reduce noise)
        """
        self.config_file = Path(config_file)
        self.logger = logger or self._setup_logger(log_level)
        self.config: OAuthConfig | None = None
        self.session = httpx.Client(timeout=30.0)

        # Yahoo OAuth endpoints
        self.auth_url = "https://api.login.yahoo.com/oauth2/request_auth"
        self.token_url = "https://api.login.yahoo.com/oauth2/get_token"

        self._load_config()

    def _setup_logger(self, log_level: int) -> logging.Logger:
        """Set up logger with configurable level."""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(log_level)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_config(self) -> None:
        """Load OAuth configuration from file."""
        if not self.config_file.exists():
            raise YahooOAuthError(f"OAuth config file not found: {self.config_file}")

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.config = OAuthConfig(**data)
            self.logger.debug("OAuth configuration loaded successfully")

        except json.JSONDecodeError as e:
            raise YahooOAuthError(f"Invalid JSON in config file: {e}") from e
        except Exception as e:
            raise YahooOAuthError(f"Error loading config: {e}") from e

    def _save_config(self) -> None:
        """Save current OAuth configuration to file."""
        if not self.config:
            raise YahooOAuthError("No configuration to save")

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config.model_dump(), f, indent=4)

            self.logger.debug("OAuth configuration saved successfully")

        except Exception as e:
            raise YahooOAuthError(f"Error saving config: {e}") from e

    def is_token_valid(self) -> bool:
        """
        Check if the current access token is valid.

        Returns:
            True if token exists and is not expired, False otherwise
        """
        if not self.config or not self.config.access_token:
            self.logger.debug("No access token available")
            return False

        if not self.config.token_time:
            self.logger.debug("No token timestamp available")
            return False

        # Yahoo tokens typically expire after 1 hour (3600 seconds)
        # We'll refresh 5 minutes early to be safe
        token_age = time.time() - self.config.token_time
        is_valid = token_age < 3300  # 55 minutes

        if not is_valid:
            self.logger.debug("Token expired (age: %.0fs)", token_age)
        else:
            self.logger.debug("Token is valid (age: %.0fs)", token_age)

        return is_valid

    def refresh_access_token(self) -> None:
        """
        Refresh the access token using the refresh token.

        Raises:
            YahooOAuthError: If refresh fails or no refresh token available
        """
        if not self.config or not self.config.refresh_token:
            raise YahooOAuthError("No refresh token available")

        self.logger.info("Refreshing access token...")

        data = {
            "client_id": self.config.consumer_key,
            "client_secret": self.config.consumer_secret,
            "refresh_token": self.config.refresh_token,
            "grant_type": "refresh_token",
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "MFL-Prop-Bets/1.0",
        }

        try:
            response = self.session.post(self.token_url, data=data, headers=headers)
            response.raise_for_status()

            token_data = response.json()

            # Update configuration with new token
            self.config.access_token = token_data["access_token"]
            self.config.token_time = time.time()

            # Update refresh token if provided
            if "refresh_token" in token_data:
                self.config.refresh_token = token_data["refresh_token"]

            self._save_config()
            self.logger.info("Access token refreshed successfully")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error refreshing token: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error_description" in error_data:
                    error_msg += f" - {error_data['error_description']}"
            except Exception:  # pylint: disable=broad-except
                pass

            self.logger.error(error_msg)
            raise YahooOAuthError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error refreshing token: {e}"
            self.logger.error(error_msg)
            raise YahooOAuthError(error_msg) from e

    def ensure_valid_token(self) -> None:
        """
        Ensure we have a valid access token, refreshing if necessary.

        Raises:
            YahooOAuthError: If unable to obtain a valid token
        """
        if not self.is_token_valid():
            self.refresh_access_token()

    def get_session(self) -> httpx.Client:
        """
        Get an HTTP session with proper authentication headers.

        Returns:
            Configured httpx.Client with authentication headers
        """
        self.ensure_valid_token()

        if not self.config or not self.config.access_token:
            raise YahooOAuthError("No valid access token available")

        # Create a new session with auth headers
        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "User-Agent": "MFL-Prop-Bets/1.0",
            "Accept": "application/json",
        }

        session = httpx.Client(timeout=30.0, headers=headers)
        return session

    def make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Make an authenticated request to Yahoo API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            **kwargs: Additional arguments to pass to the request

        Returns:
            HTTP response object

        Raises:
            YahooOAuthError: If request fails
        """
        with self.get_session() as session:
            try:
                self.logger.debug(f"Making {method} request to {url}")
                response = session.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code} error: {url}"
                self.logger.error(error_msg)
                raise YahooOAuthError(error_msg) from e

            except Exception as e:
                error_msg = f"Request failed: {e}"
                self.logger.error(error_msg)
                raise YahooOAuthError(error_msg) from e

    def get(self, url: str, **kwargs) -> httpx.Response:
        """Make authenticated GET request."""
        return self.make_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        """Make authenticated POST request."""
        return self.make_request("POST", url, **kwargs)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if hasattr(self, "session"):
            self.session.close()

    def get_auth_url(self, redirect_uri: str, state: str | None = None) -> str:
        """
        Generate authorization URL for initial OAuth setup.

        Args:
            redirect_uri: Redirect URI after authorization
            state: Optional state parameter for security

        Returns:
            Authorization URL
        """
        if not self.config:
            raise YahooOAuthError("Configuration not loaded")

        params = {
            "client_id": self.config.consumer_key,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "fspt-r",  # Fantasy Sports read permission
        }

        if state:
            params["state"] = state

        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> None:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: The same redirect URI used in authorization

        Raises:
            YahooOAuthError: If token exchange fails
        """
        if not self.config:
            raise YahooOAuthError("Configuration not loaded")

        data = {
            "client_id": self.config.consumer_key,
            "client_secret": self.config.consumer_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "MFL-Prop-Bets/1.0",
        }

        try:
            response = self.session.post(self.token_url, data=data, headers=headers)
            response.raise_for_status()

            token_data = response.json()

            # Update configuration with tokens
            self.config.access_token = token_data["access_token"]
            self.config.refresh_token = token_data.get("refresh_token")
            self.config.token_time = time.time()

            self._save_config()
            self.logger.info("Successfully exchanged code for tokens")

        except Exception as e:
            error_msg = f"Failed to exchange code for token: {e}"
            self.logger.error(error_msg)
            raise YahooOAuthError(error_msg) from e

"""Simple Yahoo OAuth token refresh utility."""

import json
import logging
from pathlib import Path

from mfl_prop_bets.clients.oauth_client import YahooOAuth


def refresh_token(config_file: str = "oauth.json") -> str:
    """
    Refresh Yahoo OAuth token and return the current access token.

    Args:
        config_file: Path to OAuth configuration file

    Returns:
        Current valid access token

    Raises:
        Exception: If token refresh fails
    """
    try:
        # Initialize OAuth client
        oauth_client = YahooOAuth(config_file=config_file, log_level=logging.INFO)

        # Ensure we have a valid token (refreshes if needed)
        oauth_client.ensure_valid_token()

        # Return the current access token
        if oauth_client.config and oauth_client.config.access_token:
            print("Token refresh successful!")
            return oauth_client.config.access_token
        else:
            raise Exception("No access token available")

    except Exception as e:
        print(f"Token refresh failed: {e}")
        raise


def get_current_token(config_file: str = "oauth.json") -> str | None:
    """
    Get the current access token without refreshing.

    Args:
        config_file: Path to OAuth configuration file

    Returns:
        Current access token or None if not available
    """
    try:
        config_path = Path(config_file)
        if not config_path.exists():
            print(f"Config file not found: {config_file}")
            return None

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("access_token")

    except Exception as e:
        print(f"Error reading token: {e}")
        return None


def main() -> None:
    """Main function to refresh token and display it."""
    try:
        # Refresh and get new token
        token = refresh_token()
        print(f"\nCurrent access token:\n{token}")
        print(f"\nToken saved to oauth.json")

    except Exception as e:
        print(f"Failed to refresh token: {e}")


if __name__ == "__main__":
    main()

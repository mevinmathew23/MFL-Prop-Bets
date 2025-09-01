"""Module for Yahoo API authorization and league management."""

import json
import logging
from typing import Any

from mfl_prop_bets.clients.oauth_client import YahooOAuth

# Module-level variables
oauth_client = None
yahoo_api = None


class YahooApi:
    """Yahoo API client for fantasy sports."""

    def __init__(self, consumer_key: str, consumer_secret: str, log_level: int = logging.INFO) -> None:
        """Initialize Yahoo API client with consumer credentials."""
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._log_level = log_level
        # self._access_token = access_token
        self._authorization = None

    def _login(self) -> None:
        """Login to Yahoo API using OAuth."""
        global oauth_client
        oauth_client = YahooOAuth(config_file="./oauth.json", log_level=self._log_level)
        oauth_client.ensure_valid_token()


class Authorize:
    """Authorization handler for Yahoo Fantasy Sports leagues."""

    def authorize_league(self) -> None:
        """Authorize and authenticate with Yahoo Fantasy Sports league."""
        # UPDATE LEAGUE GAME ID
        global yahoo_api, oauth_client
        if yahoo_api:
            yahoo_api._login()  # pylint: disable=protected-access
        url = "https://fantasysports.yahooapis.com/fantasy/v2/league/380.l.XXXXXX/transactions"
        if oauth_client:
            response = oauth_client.get(url, params={"format": "json"})
            _ = response.json()  # Response data not used
        # with open('YahooGameInfo.json', 'w') as outfile:
        # json.dump(r, outfile)
        # return;


def main() -> None:
    """Main function to initialize and run Yahoo API authorization."""
    ##### Get Yahoo Auth ####

    # Yahoo Keys
    with open("./oauth.json", encoding="utf-8") as json_yahoo_file:
        auths = json.load(json_yahoo_file)
    yahoo_consumer_key = auths["consumer_key"]
    yahoo_consumer_secret = auths["consumer_secret"]
    # yahoo_access_token = auths['access_token']
    # yahoo_access_secret = auths['access_token_secret']
    json_yahoo_file.close()

    #### Declare Yahoo Variable ####

    global yahoo_api
    yahoo_api = YahooApi(
        yahoo_consumer_key,
        yahoo_consumer_secret,
        # yahoo_access_token,
        # yahoo_access_secret)
    )
    #### Where the magic happen ####
    bot = Bot(yahoo_api)
    bot.run()


class Bot:
    """Bot class to handle Yahoo API operations."""

    def __init__(self, yahoo_api_instance: Any) -> None:
        """Initialize Bot with Yahoo API instance."""

        self._yahoo_api = yahoo_api_instance

    def run(self) -> None:
        """Run the bot authorization process."""
        # Data Updates
        at = Authorize()
        at.authorize_league()
        print("Authorization Complete")


if __name__ == "__main__":
    main()

"""Yahoo Fantasy Sports API client."""

import logging
from typing import Any

from tqdm import tqdm

from mfl_prop_bets.models import Player, Team, YearConfig
from mfl_prop_bets.clients.oauth_client import YahooOAuth


class YahooClient:
    """Client for interacting with Yahoo Fantasy Sports API."""

    def __init__(
        self,
        year_config: YearConfig,
        oauth_file: str,
        logger: logging.Logger | None = None,
        log_level: int = logging.WARNING,
    ) -> None:
        """Initialize Yahoo client with league configuration."""
        self.year_config = year_config
        self.oauth_file = oauth_file
        self.logger = logger or logging.getLogger(__name__)
        self.oauth = YahooOAuth(
            config_file=oauth_file, logger=self.logger, log_level=log_level
        )

    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid OAuth token."""
        try:
            self.oauth.ensure_valid_token()
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise

    def get_player_stats(self, player_id: str, week: str) -> float:
        """Get player statistics for a given week."""
        self._ensure_authenticated()
        url: str = (
            f"https://fantasysports.yahooapis.com/fantasy/v2/league/"
            f"{self.year_config.game_id}.l.{self.year_config.league_id}/"
            f"players;player_keys={self.year_config.game_id}.p.{player_id}/"
            f"stats;type=week;week={week}"
        )

        response = self.oauth.get(url, params={"format": "json"})
        try:
            r: dict[str, Any] = response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response for player stats: {e}")
            raise

        player_data: dict[str, Any] = r["fantasy_content"]["league"][1]["players"]["0"][
            "player"
        ][1]
        points: str = player_data["player_points"]["total"]
        return float(points)

    def get_team_info(self, tid: str, week: str, prop_position: str, all_players: bool = False) -> Team:
        """Get team information for a given week and prop position.
        
        Args:
            tid: Team ID
            week: Fantasy week number
            prop_position: Position to get prop stats for (e.g. 'QB', 'RB', etc.)
            all_players: If True, fetch stats for all players (for debugging). 
                        If False (default), only fetch stats for players matching prop_position.
        
        Returns:
            Team object with player information and stats
        """
        self._ensure_authenticated()
        url: str = (
            f"https://fantasysports.yahooapis.com/fantasy/v2/team/"
            f"{self.year_config.game_id}.l.{self.year_config.league_id}.t.{tid}/"
            f"roster;week={week}"
        )

        response = self.oauth.get(url, params={"format": "json"})
        try:
            r: dict[str, Any] = response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response for team info: {e}")
            raise

        player_count: int = r["fantasy_content"]["team"][1]["roster"]["0"]["players"][
            "count"
        ]
        players_data: dict[str, Any] = r["fantasy_content"]["team"][1]["roster"]["0"][
            "players"
        ]

        team: Team = Team(
            tid=tid,
            team_name=r["fantasy_content"]["team"][0][2]["name"],
            manager=r["fantasy_content"]["team"][0][-1]["managers"][0]["manager"][
                "nickname"
            ],
        )

        # Process players with progress bar
        with tqdm(
            range(player_count),
            desc=f"  Loading {(team.team_name or '')[:15]}... players",
            unit="player",
            leave=False,
            position=1,
        ) as player_pbar:
            for i in player_pbar:
                player_data = players_data[str(i)]

                # Find primary position
                primary_position = None
                for item in player_data["player"][0]:
                    if isinstance(item, dict) and "primary_position" in item:
                        primary_position = item["primary_position"]
                        break

                player_name = player_data["player"][0][2]["name"]["full"]
                player_pbar.set_postfix(
                    {
                        "Player": (
                            player_name[:20] + "..."
                            if len(player_name) > 20
                            else player_name
                        )
                    }
                )

                player = Player(
                    player_id=player_data["player"][0][1]["player_id"],
                    name=player_name,
                    selected_position=player_data["player"][1]["selected_position"][1][
                        "position"
                    ],
                    primary_position=primary_position,
                    keeper=(
                        player_data["player"][1]["is_keeper"]["status"]
                        if player_data["player"][1]["is_keeper"]["status"]
                        else False
                    ),
                )

                # Only fetch player stats if:
                # 1. all_players=True (for debugging), or
                # 2. player's selected position matches the prop position
                if player.player_id and (all_players or player.selected_position == prop_position):
                    player.points = self.get_player_stats(player.player_id, week)
                
                team.players.append(player)

        team.prop_total = self._calculate_prop_total(team, prop_position)
        return team

    def _calculate_prop_total(self, team: Team, prop_position: str) -> float:
        """Calculate the prop bet total for a team and position."""
        prop_total = 0.0
        team.prop_players = []

        if "|" in prop_position:
            positions = prop_position.split("|")
        else:
            positions = [prop_position]

        for player in team.players:
            include_player = False

            # Check if player's selected position matches any of the prop positions
            if player.selected_position in positions:
                include_player = True

            # Special case for TE in W/R/T slot
            if (
                prop_position == "TE"
                and player.selected_position == "W/R/T"
                and player.primary_position == "TE"
            ):
                include_player = True

            if include_player and player.points is not None:
                prop_total += player.points
                team.prop_players.append(player)

        return prop_total

"""Pydantic models for MFL Prop Bets application."""

from pydantic import BaseModel


class YearConfig(BaseModel):
    """Configuration for a specific year."""

    league_id: str
    game_id: str
    team_ids: list[str]
    sheet_id: str


class Player(BaseModel):
    """Player data model."""

    player_id: str | None = None
    name: str | None = None
    selected_position: str | None = None
    primary_position: str | None = None
    points: float | None = None
    keeper: bool | None = False


class Matchup(BaseModel):
    """Matchup data model."""

    week: int | None = None
    week_total: float = 0.0
    opp_tid: str | None = None
    opponent_total: float = 0.0
    margin: float = 0.0


class Team(BaseModel):
    """Team data model."""

    team_name: str | None = None
    tid: str | None = None
    manager: str | None = None
    players: list[Player] = []
    prop_total: float = 0.0
    prop_players: list[Player] = []
    keeper_players: list[Player] = []
    matchup: Matchup | None = None
    prop_win: bool = False
    botw_win: bool = False

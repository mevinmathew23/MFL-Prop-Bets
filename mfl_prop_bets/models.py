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


class Team(BaseModel):
    """Team data model."""
    team_name: str | None = None
    tid: str | None = None
    manager: str | None = None
    players: list[Player] = []
    prop_total: float = 0.0
    prop_players: list[Player] = []

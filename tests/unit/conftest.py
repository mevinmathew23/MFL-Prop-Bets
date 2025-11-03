"""Pytest fixtures for unit tests."""

import pytest
from unittest.mock import Mock, MagicMock

from mfl_prop_bets.models import Player, Team, Matchup, YearConfig


@pytest.fixture
def mock_year_config():
    """Create a mock YearConfig."""
    return YearConfig(
        league_id="test_league_123",
        game_id="test_game_456",
        team_ids=["test_team_1", "test_team_2", "test_team_3"],
        sheet_id="test_sheet_id_789",
    )


@pytest.fixture
def mock_prop_bet_settings(mock_year_config):
    """Create a mock PropBetSettings."""
    mock_settings = Mock()
    mock_settings.oauth_file = "test_oauth.json"
    mock_settings.service_account_file = "test_service_account.json"
    mock_settings.google_sheets_scope = ["test_scope"]
    mock_settings.get_year_config.return_value = mock_year_config
    return mock_settings


@pytest.fixture
def sample_player():
    """Create a sample player."""
    return Player(
        player_id="test_player_qb_001",
        name="Test Player",
        selected_position="QB",
        primary_position="QB",
        points=25.5,
    )


@pytest.fixture
def sample_player_rb():
    """Create a sample RB player."""
    return Player(
        player_id="test_player_rb_002",
        name="Test RB",
        selected_position="RB",
        primary_position="RB",
        points=18.2,
    )


@pytest.fixture
def sample_player_k():
    """Create a sample K player."""
    return Player(
        player_id="test_player_k_003",
        name="Test Kicker",
        selected_position="K",
        primary_position="K",
        points=10.0,
    )


@pytest.fixture
def sample_player_def():
    """Create a sample DEF player."""
    return Player(
        player_id="test_player_def_004",
        name="Test Defense",
        selected_position="DEF",
        primary_position="DEF",
        points=15.0,
    )


@pytest.fixture
def sample_matchup():
    """Create a sample matchup."""
    return Matchup(
        week=1,
        week_total=120.5,
        opp_tid="test_team_opp",
        opponent_total=95.3,
        margin=25.2,
    )


@pytest.fixture
def sample_team(sample_player, sample_matchup):
    """Create a sample team."""
    return Team(
        team_name="Test Team",
        tid="test_team_1",
        manager="Test Manager",
        players=[sample_player],
        prop_total=25.5,
        prop_players=[sample_player],
        matchup=sample_matchup,
    )


@pytest.fixture
def mock_yahoo_client(mock_year_config):
    """Create a mock YahooClient."""
    mock_client = Mock()
    mock_client.year_config = mock_year_config
    return mock_client


@pytest.fixture
def mock_sheets_client():
    """Create a mock SheetsClient."""
    mock_client = Mock()
    mock_client.update_worksheet = Mock()
    return mock_client


@pytest.fixture
def yahoo_api_roster_response():
    """Create a mock Yahoo API roster response."""
    return {
        "fantasy_content": {
            "team": [
                [
                    {"team_key": "test_game.l.test_league.t.test_team_1"},
                    {"team_id": "test_team_1"},
                    {"name": "Test Team"},
                ],
                {
                    "roster": {
                        "0": {
                            "players": {
                                "count": 2,
                                "0": {
                                    "player": [
                                        [
                                            {"player_key": "test_game.p.test_player_qb_001"},
                                            {"player_id": "test_player_qb_001"},
                                            {"name": {"full": "Test Player"}},
                                            {"primary_position": "QB"},
                                        ],
                                        {
                                            "selected_position": [
                                                {"coverage_type": "week"},
                                                {"position": "QB"},
                                            ]
                                        },
                                    ]
                                },
                                "1": {
                                    "player": [
                                        [
                                            {"player_key": "test_game.p.test_player_rb_002"},
                                            {"player_id": "test_player_rb_002"},
                                            {"name": {"full": "Test RB"}},
                                            {"primary_position": "RB"},
                                        ],
                                        {
                                            "selected_position": [
                                                {"coverage_type": "week"},
                                                {"position": "RB"},
                                            ]
                                        },
                                    ]
                                },
                            }
                        }
                    }
                },
                {"managers": [{"manager": {"nickname": "Test Manager"}}]},
            ]
        }
    }


@pytest.fixture
def yahoo_api_player_stats_response():
    """Create a mock Yahoo API player stats response."""
    return {
        "fantasy_content": {
            "league": [
                {"league_key": "test_game.l.test_league"},
                {
                    "players": {
                        "0": {
                            "player": [
                                [{"player_key": "test_game.p.test_player_qb_001"}],
                                {"player_points": {"total": "25.5"}},
                            ]
                        }
                    }
                },
            ]
        }
    }


@pytest.fixture
def yahoo_api_matchup_response():
    """Create a mock Yahoo API matchup response."""
    return {
        "fantasy_content": {
            "team": [
                [{"team_key": "test_game.l.test_league.t.test_team_1"}],
                {
                    "matchups": {
                        "0": {
                            "matchup": {
                                "0": {
                                    "teams": {
                                        "0": {
                                            "team": [
                                                [{"team_id": "test_team_1"}],
                                                {"team_points": {"total": "120.5"}},
                                            ]
                                        },
                                        "1": {
                                            "team": [
                                                [{"team_id": "test_team_2"}],
                                                {"team_points": {"total": "95.3"}},
                                            ]
                                        },
                                    }
                                }
                            }
                        }
                    }
                },
            ]
        }
    }

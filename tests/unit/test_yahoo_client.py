"""Unit tests for YahooClient."""

import pytest
from unittest.mock import Mock, patch

from mfl_prop_bets.clients.yahoo_client import YahooClient
from mfl_prop_bets.models import Team, Player


@pytest.fixture
def yahoo_client(mock_year_config):
    """Create a YahooClient instance for testing."""
    with patch("mfl_prop_bets.clients.yahoo_client.YahooOAuth"):
        client = YahooClient(
            year_config=mock_year_config, oauth_file="test_oauth.json"
        )
        client.oauth = Mock()
        return client


@pytest.mark.parametrize(
    "player_id,week,expected_points",
    [
        ("test_player_001", "1", 25.5),
        ("test_player_002", "5", 18.2),
        ("test_player_003", "10", 0.0),
    ],
)
def test_get_player_stats_returns_correct_points(
    yahoo_client, player_id, week, expected_points
):
    """Test that get_player_stats returns the correct point values."""
    yahoo_api_response = {
        "fantasy_content": {
            "league": [
                {"league_key": "test_game.l.test_league"},
                {
                    "players": {
                        "0": {
                            "player": [
                                [{"player_key": f"test_game.p.{player_id}"}],
                                {"player_points": {"total": str(expected_points)}},
                            ]
                        }
                    }
                },
            ]
        }
    }

    mock_response = Mock()
    mock_response.json.return_value = yahoo_api_response
    yahoo_client.oauth.get.return_value = mock_response
    yahoo_client.oauth.ensure_valid_token = Mock()

    points = yahoo_client.get_player_stats(player_id, week)

    assert points == expected_points
    assert isinstance(points, float)


@pytest.mark.parametrize(
    "position,players_data,expected_count",
    [
        # Single QB position - only QB should be counted
        (
            "QB",
            [("QB", "QB", 25.5), ("RB", "RB", 15.0), ("WR", "WR", 12.0)],
            1,
        ),
        # Multiple RBs
        (
            "RB",
            [("RB", "RB", 18.2), ("RB", "RB", 16.5), ("QB", "QB", 25.5)],
            2,
        ),
        # K|DEF should count both K and DEF
        (
            "K|DEF",
            [("K", "K", 10.0), ("DEF", "DEF", 15.0), ("QB", "QB", 25.5)],
            2,
        ),
        # Empty list
        ("QB", [], 0),
    ],
)
def test_calculate_prop_total_counts_correct_players(
    yahoo_client, position, players_data, expected_count
):
    """Test that prop total calculation includes only the correct players."""
    team = Team(tid="1", team_name="Test Team", manager="Test Manager")

    for selected_pos, primary_pos, points in players_data:
        player = Player(
            player_id=f"player_{selected_pos}_{points}",
            name=f"Test {selected_pos}",
            selected_position=selected_pos,
            primary_position=primary_pos,
            points=points,
        )
        team.players.append(player)

    prop_total = yahoo_client._calculate_prop_total(team, position)

    assert len(team.prop_players) == expected_count

    # Verify prop total matches sum of included players
    expected_total = sum(
        points
        for selected_pos, _, points in players_data
        if selected_pos in (position.split("|") if "|" in position else [position])
    )
    assert prop_total == expected_total


@pytest.mark.parametrize(
    "position,players_data,expected_total",
    [
        ("QB", [("QB", 25.5)], 25.5),
        ("RB", [("RB", 18.2), ("RB", 16.5)], 34.7),
        ("K|DEF", [("K", 10.0), ("DEF", 15.0)], 25.0),
        (
            "WR",
            [("WR", 12.5), ("WR", 14.0), ("WR", 8.5)],
            35.0,
        ),
    ],
)
def test_calculate_prop_total_sums_correctly(
    yahoo_client, position, players_data, expected_total
):
    """Test that prop totals are summed correctly for different positions."""
    team = Team(tid="1", team_name="Test Team", manager="Test Manager")

    for pos, points in players_data:
        player = Player(
            player_id=f"player_{pos}",
            name=f"Test {pos}",
            selected_position=pos,
            primary_position=pos,
            points=points,
        )
        team.players.append(player)

    prop_total = yahoo_client._calculate_prop_total(team, position)

    assert prop_total == pytest.approx(expected_total, rel=0.01)


def test_calculate_prop_total_te_in_flex_slot_is_counted():
    """Test that TE in W/R/T flex slot is counted for TE prop bets."""
    with patch("mfl_prop_bets.clients.yahoo_client.YahooOAuth"):
        client = YahooClient(
            year_config=Mock(league_id="test_league_123", game_id="test_game_456"),
            oauth_file="test.json",
        )

    team = Team(tid="test_team_1", team_name="Test Team", manager="Test Manager")

    # TE in flex slot
    flex_te = Player(
        player_id="test_player_te_flex",
        name="Flex TE",
        selected_position="W/R/T",
        primary_position="TE",
        points=15.5,
    )
    team.players.append(flex_te)

    # Regular TE
    regular_te = Player(
        player_id="test_player_te_regular",
        name="Regular TE",
        selected_position="TE",
        primary_position="TE",
        points=12.0,
    )
    team.players.append(regular_te)

    # WR in flex (should not be counted)
    flex_wr = Player(
        player_id="test_player_wr_flex",
        name="Flex WR",
        selected_position="W/R/T",
        primary_position="WR",
        points=18.0,
    )
    team.players.append(flex_wr)

    prop_total = client._calculate_prop_total(team, "TE")

    # Both TEs should be counted, WR should not
    assert prop_total == 27.5
    assert len(team.prop_players) == 2
    assert all(p.primary_position == "TE" for p in team.prop_players)


def test_calculate_prop_total_excludes_none_points():
    """Test that players with None points (bench/inactive) are excluded."""
    with patch("mfl_prop_bets.clients.yahoo_client.YahooOAuth"):
        client = YahooClient(
            year_config=Mock(league_id="test_league_123", game_id="test_game_456"),
            oauth_file="test.json",
        )

    team = Team(tid="test_team_1", team_name="Test Team", manager="Test Manager")

    # Active QB with points
    active_qb = Player(
        player_id="test_player_qb_active_1",
        name="Active QB",
        selected_position="QB",
        primary_position="QB",
        points=25.5,
    )
    team.players.append(active_qb)

    # Bench QB with None points
    bench_qb = Player(
        player_id="test_player_qb_bench",
        name="Bench QB",
        selected_position="QB",
        primary_position="QB",
        points=None,
    )
    team.players.append(bench_qb)

    # Another active QB
    active_qb2 = Player(
        player_id="test_player_qb_active_2",
        name="Active QB 2",
        selected_position="QB",
        primary_position="QB",
        points=18.0,
    )
    team.players.append(active_qb2)

    prop_total = client._calculate_prop_total(team, "QB")

    # Only players with points should be counted
    assert prop_total == 43.5
    assert len(team.prop_players) == 2
    assert all(p.points is not None for p in team.prop_players)


@pytest.mark.parametrize(
    "week_total,opponent_total",
    [
        (120.5, 95.3),
        (100.0, 100.0),
        (85.5, 115.0),
        (0.0, 50.0),
    ],
)
def test_calculate_matchup_total_returns_correct_values(
    yahoo_client, week_total, opponent_total
):
    """Test that matchup calculation returns correct totals and margin."""
    yahoo_api_response = {
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
                                                [{"team_key": "test_game.l.test_league.t.test_team_1"}, {"team_id": "test_team_1"}],
                                                {"team_points": {"total": str(week_total)}},
                                            ]
                                        },
                                        "1": {
                                            "team": [
                                                [{"team_key": "test_game.l.test_league.t.test_team_2"}, {"team_id": "test_team_2"}],
                                                {
                                                    "team_points": {
                                                        "total": str(opponent_total)
                                                    }
                                                },
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

    mock_response = Mock()
    mock_response.json.return_value = yahoo_api_response
    yahoo_client.oauth.get.return_value = mock_response
    yahoo_client.oauth.ensure_valid_token = Mock()

    team = Team(tid="test_team_1", team_name="Test Team")
    matchup = yahoo_client._calculate_matchup_total(team, "1")

    assert matchup.week_total == week_total
    assert matchup.opponent_total == opponent_total
    assert matchup.margin == pytest.approx(week_total - opponent_total, rel=0.01)
    assert matchup.opp_tid == "test_team_2"


def test_get_team_info_returns_complete_team_object(yahoo_client):
    """Test that get_team_info returns a fully populated Team object."""
    roster_response = {
        "fantasy_content": {
            "team": [
                [
                    {"team_key": "test_game.l.test_league.t.test_team_1"},
                    {"team_id": "test_team_1"},
                    {"name": "Test Team"},
                    {"managers": [{"manager": {"nickname": "Test Manager"}}]},
                ],
                {
                    "roster": {
                        "0": {
                            "players": {
                                "count": 2,
                                "0": {
                                    "player": [
                                        [
                                            {"player_key": "test_game.p.test_player_qb"},
                                            {"player_id": "test_player_qb"},
                                            {"name": {"full": "QB Player"}},
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
                                            {"player_key": "test_game.p.test_player_rb"},
                                            {"player_id": "test_player_rb"},
                                            {"name": {"full": "RB Player"}},
                                            {"primary_position": "RB"},
                                        ],
                                        {
                                            "selected_position": [
                                                {"coverage_type": "week"},
                                                {"position": "BN"},
                                            ]
                                        },
                                    ]
                                },
                            }
                        }
                    }
                },
            ]
        }
    }

    matchup_response = {
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
                                                [{"team_key": "test_game.l.test_league.t.test_team_1"}, {"team_id": "test_team_1"}],
                                                {"team_points": {"total": "120.5"}},
                                            ]
                                        },
                                        "1": {
                                            "team": [
                                                [{"team_key": "test_game.l.test_league.t.test_team_2"}, {"team_id": "test_team_2"}],
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

    mock_roster_resp = Mock()
    mock_roster_resp.json.return_value = roster_response
    mock_matchup_resp = Mock()
    mock_matchup_resp.json.return_value = matchup_response

    yahoo_client.oauth.get.side_effect = [mock_roster_resp, mock_matchup_resp]
    yahoo_client.oauth.ensure_valid_token = Mock()
    yahoo_client.get_player_stats = Mock(return_value=25.5)

    team = yahoo_client.get_team_info("test_team_1", "1", "QB")

    # Verify team metadata
    assert team.team_name == "Test Team"
    assert team.tid == "test_team_1"
    assert team.manager == "Test Manager"

    # Verify players were loaded
    assert len(team.players) == 2
    assert team.players[0].name == "QB Player"
    assert team.players[1].name == "RB Player"

    # Verify matchup was calculated
    assert team.matchup is not None
    assert team.matchup.week_total == 120.5

    # Verify prop total was calculated
    assert isinstance(team.prop_total, float)


def test_get_team_info_with_pipe_position_fetches_multiple_positions(yahoo_client):
    """Test that K|DEF position fetches stats for both K and DEF players."""
    roster_response = {
        "fantasy_content": {
            "team": [
                [
                    {"team_key": "test_game.l.test_league.t.test_team_1"},
                    {"team_id": "test_team_1"},
                    {"name": "Test Team"},
                    {"managers": [{"manager": {"nickname": "Test Manager"}}]},
                ],
                {
                    "roster": {
                        "0": {
                            "players": {
                                "count": 3,
                                "0": {
                                    "player": [
                                        [
                                            {"player_key": "test_game.p.test_player_k"},
                                            {"player_id": "test_player_k"},
                                            {"name": {"full": "Kicker"}},
                                            {"primary_position": "K"},
                                        ],
                                        {
                                            "selected_position": [
                                                {"coverage_type": "week"},
                                                {"position": "K"},
                                            ]
                                        },
                                    ]
                                },
                                "1": {
                                    "player": [
                                        [
                                            {"player_key": "test_game.p.test_player_def"},
                                            {"player_id": "test_player_def"},
                                            {"name": {"full": "Defense"}},
                                            {"primary_position": "DEF"},
                                        ],
                                        {
                                            "selected_position": [
                                                {"coverage_type": "week"},
                                                {"position": "DEF"},
                                            ]
                                        },
                                    ]
                                },
                                "2": {
                                    "player": [
                                        [
                                            {"player_key": "test_game.p.test_player_qb"},
                                            {"player_id": "test_player_qb"},
                                            {"name": {"full": "Quarterback"}},
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
                            }
                        }
                    }
                },
            ]
        }
    }

    matchup_response = {
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
                                                [{"team_key": "test_game.l.test_league.t.test_team_1"}, {"team_id": "test_team_1"}],
                                                {"team_points": {"total": "100.0"}},
                                            ]
                                        },
                                        "1": {
                                            "team": [
                                                [{"team_key": "test_game.l.test_league.t.test_team_2"}, {"team_id": "test_team_2"}],
                                                {"team_points": {"total": "95.0"}},
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

    mock_roster_resp = Mock()
    mock_roster_resp.json.return_value = roster_response
    mock_matchup_resp = Mock()
    mock_matchup_resp.json.return_value = matchup_response

    yahoo_client.oauth.get.side_effect = [mock_roster_resp, mock_matchup_resp]
    yahoo_client.oauth.ensure_valid_token = Mock()

    # K returns 10.0, DEF returns 15.0, QB should not be called
    call_count = 0

    def mock_get_player_stats(player_id, week):
        nonlocal call_count
        call_count += 1
        if player_id == "test_player_k":  # K
            return 10.0
        elif player_id == "test_player_def":  # DEF
            return 15.0
        return 0.0

    yahoo_client.get_player_stats = mock_get_player_stats

    team = yahoo_client.get_team_info("test_team_1", "1", "K|DEF")

    # Verify only K and DEF had stats fetched (not QB)
    assert call_count == 2

    # Verify prop total includes both K and DEF
    assert team.prop_total == 25.0
    assert len(team.prop_players) == 2

    # Verify the correct players are in prop_players
    positions = {p.selected_position for p in team.prop_players}
    assert positions == {"K", "DEF"}

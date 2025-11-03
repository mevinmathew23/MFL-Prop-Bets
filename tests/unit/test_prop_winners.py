"""Unit tests for prop_winners module."""

import pytest

from mfl_prop_bets.prop_winners import determine_prop_winner, determine_botw_winner
from mfl_prop_bets.models import Team, Matchup


@pytest.mark.parametrize(
    "team_prop_totals,expected_winners",
    [
        # Single winner with highest total
        ([25.5, 18.2, 15.0], [True, False, False]),
        # Tie - both teams win
        ([25.5, 25.5, 18.2], [True, True, False]),
        # All tied - all win
        ([25.5, 25.5, 25.5], [True, True, True]),
        # Single team
        ([25.5], [True]),
        # Two teams, one winner
        ([30.0, 25.5], [True, False]),
    ],
)
def test_determine_prop_winner_identifies_correct_winners(
    team_prop_totals, expected_winners
):
    """Test that prop winners are correctly identified based on highest total."""
    teams = {}
    for i, (prop_total, expected_win) in enumerate(
        zip(team_prop_totals, expected_winners)
    ):
        teams[str(i + 1)] = Team(
            tid=str(i + 1),
            team_name=f"Team {i+1}",
            manager=f"Manager {i+1}",
            prop_total=prop_total,
            matchup=Matchup(margin=0.0),
        )

    determine_prop_winner(teams)

    for i, team in enumerate(teams.values()):
        assert (
            team.prop_win == expected_winners[i]
        ), f"Team {i+1} prop_win should be {expected_winners[i]}, got {team.prop_win}"


def test_determine_prop_winner_with_zero_totals():
    """Test prop winner determination when all totals are zero."""
    teams = {
        "1": Team(tid="1", team_name="Team 1", prop_total=0.0, matchup=Matchup()),
        "2": Team(tid="2", team_name="Team 2", prop_total=0.0, matchup=Matchup()),
        "3": Team(tid="3", team_name="Team 3", prop_total=0.0, matchup=Matchup()),
    }

    determine_prop_winner(teams)

    # All teams should win when tied at 0
    for team in teams.values():
        assert team.prop_win is True


def test_determine_prop_winner_with_negative_margin():
    """Test that prop winner is based on prop_total, not matchup margin."""
    teams = {
        "1": Team(
            tid="1",
            team_name="Team 1",
            prop_total=30.0,
            matchup=Matchup(margin=-10.0),  # Lost matchup
        ),
        "2": Team(
            tid="2",
            team_name="Team 2",
            prop_total=20.0,
            matchup=Matchup(margin=15.0),  # Won matchup
        ),
    }

    determine_prop_winner(teams)

    # Team 1 should win prop despite losing matchup
    assert teams["1"].prop_win is True
    assert teams["2"].prop_win is False


@pytest.mark.parametrize(
    "team_margins,expected_winners",
    [
        # Single winner with highest margin
        ([25.2, 15.0, -5.5], [True, False, False]),
        # Tie - both teams win
        ([25.2, 25.2, 15.0], [True, True, False]),
        # All tied - all win
        ([10.0, 10.0, 10.0], [True, True, True]),
        # Single team
        ([5.0], [True]),
        # Negative margins - highest still wins
        ([-5.0, -10.0, -15.0], [True, False, False]),
        # Mix of positive and negative
        ([20.0, -5.0, 15.0], [True, False, False]),
    ],
)
def test_determine_botw_winner_identifies_correct_winners(team_margins, expected_winners):
    """Test that BOTW winners are correctly identified based on highest margin."""
    teams = {}
    for i, (margin, expected_win) in enumerate(zip(team_margins, expected_winners)):
        teams[str(i + 1)] = Team(
            tid=str(i + 1),
            team_name=f"Team {i+1}",
            manager=f"Manager {i+1}",
            prop_total=0.0,
            matchup=Matchup(margin=margin),
        )

    determine_botw_winner(teams)

    for i, team in enumerate(teams.values()):
        assert (
            team.botw_win == expected_winners[i]
        ), f"Team {i+1} botw_win should be {expected_winners[i]}, got {team.botw_win}"


def test_determine_botw_winner_with_zero_margins():
    """Test BOTW winner determination when all margins are zero (all tied)."""
    teams = {
        "1": Team(tid="1", team_name="Team 1", matchup=Matchup(margin=0.0)),
        "2": Team(tid="2", team_name="Team 2", matchup=Matchup(margin=0.0)),
        "3": Team(tid="3", team_name="Team 3", matchup=Matchup(margin=0.0)),
    }

    determine_botw_winner(teams)

    # All teams should win when tied at 0
    for team in teams.values():
        assert team.botw_win is True


def test_determine_botw_winner_independent_of_prop_total():
    """Test that BOTW winner is based on margin, not prop_total."""
    teams = {
        "1": Team(
            tid="1",
            team_name="Team 1",
            prop_total=50.0,  # Highest prop total
            matchup=Matchup(margin=10.0),
        ),
        "2": Team(
            tid="2",
            team_name="Team 2",
            prop_total=30.0,
            matchup=Matchup(margin=25.0),  # Highest margin
        ),
    }

    determine_botw_winner(teams)

    # Team 2 should win BOTW despite lower prop total
    assert teams["1"].botw_win is False
    assert teams["2"].botw_win is True


def test_both_winners_can_be_different_teams():
    """Test that prop winner and BOTW winner can be different teams."""
    teams = {
        "1": Team(
            tid="1",
            team_name="Team 1",
            prop_total=40.0,  # Highest prop
            matchup=Matchup(margin=10.0),
        ),
        "2": Team(
            tid="2",
            team_name="Team 2",
            prop_total=30.0,
            matchup=Matchup(margin=25.0),  # Highest margin
        ),
        "3": Team(
            tid="3",
            team_name="Team 3",
            prop_total=25.0,
            matchup=Matchup(margin=5.0),
        ),
    }

    determine_prop_winner(teams)
    determine_botw_winner(teams)

    # Team 1 wins prop
    assert teams["1"].prop_win is True
    assert teams["2"].prop_win is False
    assert teams["3"].prop_win is False

    # Team 2 wins BOTW
    assert teams["1"].botw_win is False
    assert teams["2"].botw_win is True
    assert teams["3"].botw_win is False


def test_same_team_can_win_both():
    """Test that same team can win both prop and BOTW."""
    teams = {
        "1": Team(
            tid="1",
            team_name="Team 1",
            prop_total=40.0,  # Highest
            matchup=Matchup(margin=30.0),  # Highest
        ),
        "2": Team(
            tid="2",
            team_name="Team 2",
            prop_total=30.0,
            matchup=Matchup(margin=20.0),
        ),
        "3": Team(
            tid="3",
            team_name="Team 3",
            prop_total=25.0,
            matchup=Matchup(margin=15.0),
        ),
    }

    determine_prop_winner(teams)
    determine_botw_winner(teams)

    # Team 1 wins both
    assert teams["1"].prop_win is True
    assert teams["1"].botw_win is True

    # Other teams win neither
    assert teams["2"].prop_win is False
    assert teams["2"].botw_win is False
    assert teams["3"].prop_win is False
    assert teams["3"].botw_win is False


def test_multiple_teams_can_tie_for_both():
    """Test that multiple teams can tie for both prop and BOTW."""
    teams = {
        "1": Team(
            tid="1",
            team_name="Team 1",
            prop_total=35.0,
            matchup=Matchup(margin=20.0),
        ),
        "2": Team(
            tid="2",
            team_name="Team 2",
            prop_total=35.0,
            matchup=Matchup(margin=20.0),
        ),
        "3": Team(
            tid="3",
            team_name="Team 3",
            prop_total=30.0,
            matchup=Matchup(margin=15.0),
        ),
    }

    determine_prop_winner(teams)
    determine_botw_winner(teams)

    # Teams 1 and 2 win both
    assert teams["1"].prop_win is True
    assert teams["1"].botw_win is True
    assert teams["2"].prop_win is True
    assert teams["2"].botw_win is True

    # Team 3 wins neither
    assert teams["3"].prop_win is False
    assert teams["3"].botw_win is False


def test_prop_winner_with_float_precision():
    """Test prop winner determination with float precision considerations."""
    teams = {
        "1": Team(
            tid="1",
            team_name="Team 1",
            prop_total=25.501,
            matchup=Matchup(margin=0.0),
        ),
        "2": Team(
            tid="2",
            team_name="Team 2",
            prop_total=25.500,
            matchup=Matchup(margin=0.0),
        ),
        "3": Team(
            tid="3",
            team_name="Team 3",
            prop_total=25.499,
            matchup=Matchup(margin=0.0),
        ),
    }

    determine_prop_winner(teams)

    assert teams["1"].prop_win is True
    assert teams["2"].prop_win is False
    assert teams["3"].prop_win is False


def test_botw_winner_with_float_precision():
    """Test BOTW winner determination with float precision considerations."""
    teams = {
        "1": Team(
            tid="1", team_name="Team 1", matchup=Matchup(margin=15.001)
        ),
        "2": Team(
            tid="2", team_name="Team 2", matchup=Matchup(margin=15.000)
        ),
        "3": Team(
            tid="3", team_name="Team 3", matchup=Matchup(margin=14.999)
        ),
    }

    determine_botw_winner(teams)

    assert teams["1"].botw_win is True
    assert teams["2"].botw_win is False
    assert teams["3"].botw_win is False

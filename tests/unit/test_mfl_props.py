"""Unit tests for mfl_props.py main function."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

from mfl_prop_bets.mfl_props import main
from mfl_prop_bets.models import Team, Player, Matchup


@pytest.mark.parametrize(
    "week,position,year,update",
    [
        (1, "QB", "2024", False),
        (5, "RB", "2024", False),
        (10, "WR", "2023", False),
        (6, "K|DEF", "2024", False),
    ],
)
def test_main_without_update(
    week, position, year, update, mock_prop_bet_settings, sample_team
):
    """Test main function without updating Google Sheets."""
    # Setup mocks
    with (
        patch("mfl_prop_bets.mfl_props.PropBetSettings") as mock_settings_class,
        patch("mfl_prop_bets.mfl_props.YahooClient") as mock_yahoo_class,
        patch("mfl_prop_bets.mfl_props.argparse.ArgumentParser.parse_args") as mock_args,
        patch("mfl_prop_bets.mfl_props.determine_prop_winner") as mock_prop_winner,
        patch("mfl_prop_bets.mfl_props.determine_botw_winner") as mock_botw_winner,
    ):
        # Configure mocks
        mock_settings_class.return_value = mock_prop_bet_settings
        mock_args.return_value = Namespace(
            week=week, position=position, year=year, update=update
        )

        mock_yahoo_instance = Mock()
        mock_yahoo_instance.get_team_info.return_value = sample_team
        mock_yahoo_class.return_value = mock_yahoo_instance

        # Run main
        main()

        # Verify PropBetSettings was instantiated
        mock_settings_class.assert_called_once()

        # Verify YahooClient was instantiated with correct parameters
        mock_yahoo_class.assert_called_once_with(
            year_config=mock_prop_bet_settings.get_year_config.return_value,
            oauth_file=mock_prop_bet_settings.oauth_file,
        )

        # Verify get_team_info was called for each team
        assert (
            mock_yahoo_instance.get_team_info.call_count
            == len(mock_prop_bet_settings.get_year_config.return_value.team_ids)
        )

        # Verify prop winner functions were called
        mock_prop_winner.assert_called_once()
        mock_botw_winner.assert_called_once()


@pytest.mark.parametrize(
    "week,position,year",
    [
        (1, "QB", "2024"),
        (6, "K|DEF", "2024"),
        (3, "TE", "2023"),
    ],
)
def test_main_with_update(week, position, year, mock_prop_bet_settings, sample_team):
    """Test main function with Google Sheets update."""
    with (
        patch("mfl_prop_bets.mfl_props.PropBetSettings") as mock_settings_class,
        patch("mfl_prop_bets.mfl_props.YahooClient") as mock_yahoo_class,
        patch("mfl_prop_bets.mfl_props.SheetsClient") as mock_sheets_class,
        patch("mfl_prop_bets.mfl_props.argparse.ArgumentParser.parse_args") as mock_args,
        patch("mfl_prop_bets.mfl_props.determine_prop_winner"),
        patch("mfl_prop_bets.mfl_props.determine_botw_winner"),
    ):
        # Configure mocks
        mock_settings_class.return_value = mock_prop_bet_settings
        mock_args.return_value = Namespace(
            week=week, position=position, year=year, update=True
        )

        mock_yahoo_instance = Mock()
        mock_yahoo_instance.get_team_info.return_value = sample_team
        mock_yahoo_class.return_value = mock_yahoo_instance

        mock_sheets_instance = Mock()
        mock_sheets_class.return_value = mock_sheets_instance

        # Run main
        main()

        # Verify SheetsClient was instantiated
        mock_sheets_class.assert_called_once_with(
            service_account_file=mock_prop_bet_settings.service_account_file,
            sheet_id=mock_prop_bet_settings.get_year_config.return_value.sheet_id,
            scopes=mock_prop_bet_settings.google_sheets_scope,
        )

        # Verify update_worksheet was called with correct worksheet name
        expected_worksheet_name = f"Week{week}{position}"
        mock_sheets_instance.update_worksheet.assert_called_once()
        call_args = mock_sheets_instance.update_worksheet.call_args
        assert call_args[0][0] == expected_worksheet_name


@pytest.mark.parametrize(
    "team_count",
    [1, 3, 10, 12],
)
def test_main_processes_all_teams(team_count, mock_prop_bet_settings, sample_team):
    """Test that main processes all teams in the configuration."""
    # Setup team IDs based on team_count
    team_ids = [str(i) for i in range(1, team_count + 1)]
    mock_prop_bet_settings.get_year_config.return_value.team_ids = team_ids

    with (
        patch("mfl_prop_bets.mfl_props.PropBetSettings") as mock_settings_class,
        patch("mfl_prop_bets.mfl_props.YahooClient") as mock_yahoo_class,
        patch("mfl_prop_bets.mfl_props.argparse.ArgumentParser.parse_args") as mock_args,
        patch("mfl_prop_bets.mfl_props.determine_prop_winner"),
        patch("mfl_prop_bets.mfl_props.determine_botw_winner"),
    ):
        # Configure mocks
        mock_settings_class.return_value = mock_prop_bet_settings
        mock_args.return_value = Namespace(
            week=1, position="QB", year="2024", update=False
        )

        mock_yahoo_instance = Mock()
        mock_yahoo_instance.get_team_info.return_value = sample_team
        mock_yahoo_class.return_value = mock_yahoo_instance

        # Run main
        main()

        # Verify get_team_info was called correct number of times
        assert mock_yahoo_instance.get_team_info.call_count == team_count

        # Verify all team IDs were processed
        call_args_list = mock_yahoo_instance.get_team_info.call_args_list
        processed_team_ids = [call[0][0] for call in call_args_list]
        assert sorted(processed_team_ids) == sorted(team_ids)


def test_main_handles_multiple_positions_with_pipe(
    mock_prop_bet_settings, sample_team
):
    """Test that main correctly handles multiple positions with pipe operator."""
    with (
        patch("mfl_prop_bets.mfl_props.PropBetSettings") as mock_settings_class,
        patch("mfl_prop_bets.mfl_props.YahooClient") as mock_yahoo_class,
        patch("mfl_prop_bets.mfl_props.SheetsClient") as mock_sheets_class,
        patch("mfl_prop_bets.mfl_props.argparse.ArgumentParser.parse_args") as mock_args,
        patch("mfl_prop_bets.mfl_props.determine_prop_winner"),
        patch("mfl_prop_bets.mfl_props.determine_botw_winner"),
    ):
        # Configure mocks
        mock_settings_class.return_value = mock_prop_bet_settings
        mock_args.return_value = Namespace(
            week=6, position="K|DEF", year="2024", update=True
        )

        mock_yahoo_instance = Mock()
        mock_yahoo_instance.get_team_info.return_value = sample_team
        mock_yahoo_class.return_value = mock_yahoo_instance

        mock_sheets_instance = Mock()
        mock_sheets_class.return_value = mock_sheets_instance

        # Run main
        main()

        # Verify worksheet name includes pipe
        expected_worksheet_name = "Week6K|DEF"
        mock_sheets_instance.update_worksheet.assert_called_once()
        call_args = mock_sheets_instance.update_worksheet.call_args
        assert call_args[0][0] == expected_worksheet_name

        # Verify position was passed correctly to get_team_info
        call_args_list = mock_yahoo_instance.get_team_info.call_args_list
        for call in call_args_list:
            assert call[0][2] == "K|DEF"  # position argument

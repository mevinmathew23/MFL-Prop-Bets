"""Main script for MFL Prop Bets calculator."""

import argparse
from typing import Any

from tqdm import tqdm

from mfl_prop_bets.clients.sheets_client import SheetsClient
from mfl_prop_bets.clients.yahoo_client import YahooClient
from mfl_prop_bets.models import Team
from mfl_prop_bets.settings import PropBetSettings
from mfl_prop_bets.prop_winners import determine_prop_winner, determine_botw_winner


def main() -> None:
    """Main entry point for the MFL Prop Bets application.

    Processes fantasy football team data to calculate prop bet totals for a specific
    position and week. Optionally updates a Google Sheets worksheet with the results.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Arguments for prop bets")
    parser.add_argument(
        "--week",
        default=1,
        required=True,
        type=int,
        help="Specify which Fantasy Football week prop bet is on",
    )
    parser.add_argument(
        "--position",
        required=True,
        type=str,
        help="Specify the position prop bet is for",
    )
    parser.add_argument(
        "--year",
        default="2024",
        type=str,
        help="Specify which year's league configuration to use",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        default=False,
        help="Update the Google Sheets worksheet with the calculated data",
    )

    args: argparse.Namespace = parser.parse_args()
    week: str = str(args.week)
    position: str = args.position
    year: str = args.year
    update: bool = args.update

    # Initialize settings and get configuration
    settings: PropBetSettings = PropBetSettings()
    year_config = settings.get_year_config(year)

    print(f"Using league {year_config.league_id} for game {year_config.game_id}")

    # Initialize Yahoo client
    yahoo_client: YahooClient = YahooClient(
        year_config=year_config, oauth_file=settings.oauth_file
    )

    # Get team information for all teams
    teams: dict[str, Team] = {}
    print(
        f"Processing {len(year_config.team_ids)} teams for Week {week} {position} props..."
    )

    with tqdm(year_config.team_ids, desc="Processing teams", unit="team") as team_pbar:
        for tid in team_pbar:
            team_pbar.set_postfix({"Team ID": tid})
            team: Team = yahoo_client.get_team_info(tid, week, position)
            teams[tid] = team
            team_pbar.set_postfix(
                {
                    "Team": (
                        team.team_name[:20] + "..."
                        if team.team_name and len(team.team_name) > 20
                        else team.team_name or ""
                    ),
                    "Manager": (
                        team.manager[:15] + "..."
                        if team.manager and len(team.manager) > 15
                        else team.manager or ""
                    ),
                    "Players": len(team.prop_players),
                    "Total": f"{team.prop_total:.1f}",
                }
            )

    # Determine prop winners
    determine_prop_winner(teams)
    determine_botw_winner(teams)

    # Update Google Sheet if requested
    if update:
        # Initialize sheets client only when needed
        sheets_client: SheetsClient = SheetsClient(
            service_account_file=settings.service_account_file,
            sheet_id=year_config.sheet_id,
            scopes=settings.google_sheets_scope,
        )
        worksheet_name: str = f"Week{week}{position}"
        sheets_client.update_worksheet(worksheet_name, teams)
        print(f"Updated worksheet '{worksheet_name}' with {len(teams)} teams")
    else:
        print("Use --update flag to update the Google Sheets worksheet")


if __name__ == "__main__":
    main()

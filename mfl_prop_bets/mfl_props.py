"""Main script for MFL Prop Bets calculator."""

import argparse

from tqdm import tqdm

from .clients.sheets_client import SheetsClient
from .clients.yahoo_client import YahooClient
from .settings import Settings


def main():
    """Main entry point for the application."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Arguments for prop bets')
    parser.add_argument(
        "--week",
        default=1,
        required=True,
        type=int,
        help="Specify which Fantasy Football week prop bet is on"
    )
    parser.add_argument(
        "--position",
        required=True,
        type=str,
        help="Specify the position prop bet is for"
    )
    parser.add_argument(
        "--year",
        default="2024",
        type=str,
        help="Specify which year's league configuration to use"
    )

    args = parser.parse_args()
    week = str(args.week)
    position = args.position
    year = args.year

    # Initialize settings and get configuration
    settings = Settings()
    year_config = settings.get_year_config(year)

    print(f"Using league {year_config.league_id} for game {year_config.game_id}")

    # Initialize clients
    yahoo_client = YahooClient(
        year_config=year_config,
        oauth_file=settings.OAUTH_FILE
    )

    sheets_client = SheetsClient(
        service_account_file=settings.SERVICE_ACCOUNT_FILE,
        sheet_id=year_config.sheet_id,
        scopes=settings.GOOGLE_SHEETS_SCOPE
    )

    # Get team information for all teams
    teams = []
    print(f"Processing {len(year_config.team_ids)} teams for Week {week} {position} props...")

    with tqdm(year_config.team_ids, desc="Processing teams", unit="team") as team_pbar:
        for tid in team_pbar:
            team_pbar.set_postfix({"Team ID": tid})
            team = yahoo_client.get_team_info(tid, week, position)
            teams.append(team)
            team_pbar.set_postfix({
                "Team": team.team_name[:20] + "..." if len(team.team_name) > 20 else team.team_name,
                "Manager": team.manager[:15] + "..." if len(team.manager) > 15 else team.manager,
                "Players": len(team.prop_players),
                "Total": f"{team.prop_total:.1f}"
            })

    # Update Google Sheet
    worksheet_name = f'Week{week}{position}'
    sheets_client.update_worksheet(worksheet_name, teams)

    print(f"Updated worksheet '{worksheet_name}' with {len(teams)} teams")


if __name__ == "__main__":
    main()

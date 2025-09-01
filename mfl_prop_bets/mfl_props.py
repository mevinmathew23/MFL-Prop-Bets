"""Main script for MFL Prop Bets calculator."""

import argparse

from clients.sheets_client import SheetsClient
from clients.yahoo_client import YahooClient
from settings import Settings


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
    for tid in year_config.team_ids:
        team = yahoo_client.get_team_info(tid, week, position)
        teams.append(team)
    
    # Update Google Sheet
    worksheet_name = f'Week{week}{position}'
    sheets_client.update_worksheet(worksheet_name, teams)
    
    print(f"Updated worksheet '{worksheet_name}' with {len(teams)} teams")


if __name__ == "__main__":
    main()
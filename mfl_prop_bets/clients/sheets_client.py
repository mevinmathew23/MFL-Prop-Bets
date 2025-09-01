"""Google Sheets client for updating spreadsheet data."""

import gspread
from gspread import Cell
from mfl_prop_bets.models import Team
from oauth2client.service_account import ServiceAccountCredentials


class SheetsClient:
    """Client for interacting with Google Sheets."""

    def __init__(self, service_account_file: str, sheet_id: str, scopes: list[str]):
        """Initialize Google Sheets client."""
        self.service_account_file = service_account_file
        self.sheet_id = sheet_id
        self.scopes = scopes
        self._authorize()

    def _authorize(self) -> None:
        """Authorize with Google Sheets API."""
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.service_account_file, self.scopes
        )
        self.client = gspread.authorize(credentials)

    def update_worksheet(self, worksheet_name: str, teams: list[Team]) -> None:
        """Update a worksheet with team data."""
        sheet = self.client.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet(worksheet_name)

        row_offset = 2
        cells = []

        for team in teams:
            for i, prop_player in enumerate(team.prop_players):
                current_row = row_offset + i

                # Add manager name and total only for the first player of each team
                if i == 0:
                    cells.append(Cell(row=current_row, col=1, value=team.manager))
                    cells.append(Cell(row=current_row, col=5, value=team.prop_total))

                # Add player information
                cells.append(Cell(row=current_row, col=2, value=prop_player.name))
                cells.append(
                    Cell(row=current_row, col=3, value=prop_player.selected_position)
                )
                cells.append(Cell(row=current_row, col=4, value=prop_player.points))

            # Move to next team section (add space between teams)
            row_offset += len(team.prop_players) + 2

        # Update all cells at once
        worksheet.update_cells(cells)

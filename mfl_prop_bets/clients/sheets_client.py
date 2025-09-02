"""Google Sheets client for updating spreadsheet data."""

import gspread
from gspread import Cell
from google.oauth2.service_account import Credentials

from mfl_prop_bets.models import Team


class SheetsClient:
    """Client for interacting with Google Sheets."""

    def __init__(
        self, service_account_file: str, sheet_id: str, scopes: list[str]
    ) -> None:
        """Initialize Google Sheets client."""
        self.service_account_file = service_account_file
        self.sheet_id = sheet_id
        self.scopes = scopes
        self._authorize()

    def _authorize(self) -> None:
        """Authorize with Google Sheets API."""
        credentials = Credentials.from_service_account_file(
            self.service_account_file, scopes=self.scopes
        )
        self.client = gspread.authorize(credentials)

    def update_worksheet(self, worksheet_name: str, teams: dict[str, Team]) -> None:
        """Update a worksheet with team data."""
        sheet = self.client.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet(worksheet_name)

        row_offset: int = 2
        cells: list[Cell] = []

        for team in teams.values():
            for i, prop_player in enumerate(team.prop_players):
                current_row: int = row_offset + i

                # Add manager name and total only for the first player of each team
                if i == 0:
                    cells.append(Cell(row=current_row, col=1, value=team.manager))
                    cells.append(
                        Cell(row=current_row, col=5, value=f"{team.prop_total:.2f}")
                    )
                    cells.append(
                        Cell(
                            row=current_row,
                            col=6,
                            value=f"{team.prop_win}" if team.prop_win else "",
                        )
                    )
                    cells.append(
                        Cell(
                            row=current_row,
                            col=7,
                            value=(
                                f"{team.matchup.margin:.2f}"
                                if team.matchup.margin
                                else ""
                            ),
                        )
                    )
                    cells.append(
                        Cell(
                            row=current_row,
                            col=8,
                            value=f"{team.botw_win}" if team.botw_win else "",
                        )
                    )

                # Add player information
                cells.append(Cell(row=current_row, col=2, value=prop_player.name))
                cells.append(
                    Cell(row=current_row, col=3, value=prop_player.selected_position)
                )
                cells.append(
                    Cell(
                        row=current_row,
                        col=4,
                        value=(
                            f"{prop_player.points:.2f}"
                            if prop_player.points is not None
                            else ""
                        ),
                    )
                )

            # Move to next team section (add space between teams)
            row_offset += len(team.prop_players) + 2

        # Update all cells at once
        worksheet.update_cells(cells)

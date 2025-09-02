from mfl_prop_bets.models import Team


def determine_prop_winner(teams: dict[str, Team]) -> None:
    """Determine the prop winners for a week."""
    # Find the maximum prop total across all teams
    max_prop_total = max(team.prop_total for team in teams.values())

    # A team wins if their prop total equals the maximum
    for team in teams.values():
        team.prop_win = team.prop_total == max_prop_total


def determine_botw_winner(teams: dict[str, Team]) -> None:
    """Determine the botw winners for a week."""
    max_margin = max(team.matchup.margin for team in teams.values())

    for team in teams.values():
        team.botw_win = team.matchup.margin == max_margin

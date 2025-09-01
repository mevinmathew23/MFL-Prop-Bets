"""Yahoo Fantasy Sports API client."""

from yahoo_oauth import OAuth2

from models import Player, Team, YearConfig


class YahooClient:
    """Client for interacting with Yahoo Fantasy Sports API."""
    
    def __init__(self, year_config: YearConfig, oauth_file: str):
        """Initialize Yahoo client with league configuration."""
        self.year_config = year_config
        self.oauth_file = oauth_file
        self.oauth = None
        self._login()
    
    def _login(self) -> None:
        """Authenticate with Yahoo OAuth."""
        self.oauth = OAuth2(None, None, from_file=self.oauth_file)
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()
    
    def get_player_stats(self, player_id: str, week: str) -> float:
        """Get player statistics for a given week."""
        self._login()
        url = (
            f'https://fantasysports.yahooapis.com/fantasy/v2/league/'
            f'{self.year_config.game_id}.l.{self.year_config.league_id}/'
            f'players;player_keys={self.year_config.game_id}.p.{player_id}/'
            f'stats;type=week;week={week}'
        )
        
        response = self.oauth.session.get(url, params={'format': 'json'})
        r = response.json()
        points = r['fantasy_content']['league'][1]['players']['0']['player'][1]['player_points']['total']
        return float(points)
    
    def get_team_info(self, tid: str, week: str, prop_position: str) -> Team:
        """Get team information for a given week and prop position."""
        self._login()
        url = (
            f'https://fantasysports.yahooapis.com/fantasy/v2/team/'
            f'{self.year_config.game_id}.l.{self.year_config.league_id}.t.{tid}/'
            f'roster;week={week}'
        )
        
        response = self.oauth.session.get(url, params={'format': 'json'})
        r = response.json()
        
        player_count = r['fantasy_content']['team'][1]['roster']['0']['players']['count']
        players_data = r['fantasy_content']['team'][1]['roster']['0']['players']
        
        team = Team(
            tid=tid,
            team_name=r['fantasy_content']['team'][0][2]['name'],
            manager=r['fantasy_content']['team'][0][-1]['managers'][0]['manager']['nickname']
        )
        
        for i in range(player_count):
            player_data = players_data[str(i)]
            
            # Find primary position
            primary_position = None
            for item in player_data['player'][0]:
                if isinstance(item, dict) and "primary_position" in item:
                    primary_position = item['primary_position']
                    break
            
            player = Player(
                player_id=player_data['player'][0][1]['player_id'],
                name=player_data['player'][0][2]['name']['full'],
                selected_position=player_data['player'][1]['selected_position'][1]['position'],
                primary_position=primary_position
            )
            
            player.points = self.get_player_stats(player.player_id, week)
            team.players.append(player)
        
        team.prop_total = self._calculate_prop_total(team, prop_position)
        return team
    
    def _calculate_prop_total(self, team: Team, prop_position: str) -> float:
        """Calculate the prop bet total for a team and position."""
        prop_total = 0.0
        team.prop_players = []
        
        if '|' in prop_position:
            positions = prop_position.split('|')
        else:
            positions = [prop_position]
        
        for player in team.players:
            include_player = False
            
            # Check if player's selected position matches any of the prop positions
            if player.selected_position in positions:
                include_player = True
            
            # Special case for TE in W/R/T slot
            if prop_position == 'TE' and player.selected_position == 'W/R/T' and player.primary_position == 'TE':
                include_player = True
            
            if include_player and player.points is not None:
                prop_total += player.points
                team.prop_players.append(player)
        
        return prop_total
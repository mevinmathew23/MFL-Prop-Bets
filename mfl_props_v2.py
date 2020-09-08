import pandas as pd
from yahoo_oauth import OAuth2
import json
from json import dumps
import datetime
import threading
import argparse
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Class to get Yahoo API
class Yahoo_Api():
    def __init__(self, consumer_key, consumer_secret,
                access_key):
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_key = access_key
        self._authorization = None
    def _login(self):
        global oauth
        oauth = OAuth2(None, None, from_file='./oauth.json')
        if not oauth.token_is_valid():
            oauth.refresh_access_token()

# Class for all player data
class Player():
    def __init__(self):
        self.player_id = None
        self.name = None
        self.selected_position = None
        self.points = None

# Class for all team data
class Team():
    def __init__(self):
        self.team_name = None
        self.tid = None
        self.manager = None
        self.players = []
        self.prop_total = 0
        self.prop_players = []

# Function to get each players statistic on a given week
def get_player_stats(player_id, week):
    yahoo_api._login()
    url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/%s.l.%s/players;player_keys=%s.p.%s/stats;type=week;week=%s' % (game_id, league_id, game_id, player_id, week)
    response = oauth.session.get(url, params={'format': 'json'})
    r = response.json()
    points = r['fantasy_content']['league'][1]['players']['0']['player'][1]['player_points']['total']
    # print(r['fantasy_content']['league'][1]['players']['0']['player'][1]['player_points']['total'])
    return points

# Function to return all of the team information for a given week and prop position
def get_team_info(tid, week, prop_position):
    team = Team()
    yahoo_api._login()
    url = 'https://fantasysports.yahooapis.com/fantasy/v2/team/%s.l.%s.t.%s/roster;week=%s' % (game_id, league_id, tid, week)
    response = oauth.session.get(url, params={'format': 'json'})
    r = response.json()
    # print(r['fantasy_content']['team'][1]['roster']['0']['players']['count'])
    player_count = r['fantasy_content']['team'][1]['roster']['0']['players']['count']
    # print(player_count)
    # print(r['fantasy_content']['team'][0][-1]['managers'][0]['manager']['nickname'])
    players = r['fantasy_content']['team'][1]['roster']['0']['players']
    

    team.tid = tid
    team.team_name = r['fantasy_content']['team'][0][2]['name']
    team.manager = r['fantasy_content']['team'][0][-1]['managers'][0]['manager']['nickname']

    player_list = []
    for i in range(0, player_count):
        current_player = Player()
        # print(players[str(i)])
        # print('\n')
        # print(players[str(i)]['player'][1]['selected_position'][1]['position'])
        # print('\n\n')
        current_player.player_id = players[str(i)]['player'][0][1]['player_id']
        current_player.name = players[str(i)]['player'][0][2]['name']['full']
        current_player.selected_position = players[str(i)]['player'][1]['selected_position'][1]['position']
        # current_player.is_starting = field['starting_status']['is_starting']
        current_player.points = get_player_stats(current_player.player_id, week)
        player_list.append(current_player.__dict__)

    team.players = player_list
    team.prop_total = get_prop_total(team, prop_position)
    # for player in team.players:
    #     print(player.__dict__)
    # for prop_player in team.prop_players:
    #     print(prop_player.__dict__)
    # print(json.dumps(team.__dict__))
    return team

    # Work on getting points from the player collection

# Function to get the prop bet total for the week
def get_prop_total(team, prop_position):
    prop_total = 0
    for player in team.players:
        if (player['selected_position'] == prop_position):
            prop_total += float(player['points'])
            team.prop_players.append(player)
            

    return prop_total


# Main method
def main():
    # Setting up argument parser for script
    parser = argparse.ArgumentParser(description='Arguments for prop bets')
    parser.add_argument("--week", default=1, required=True, type=int, help="Specify which Fantasy Football week prop bet is on")
    parser.add_argument("--position", required=True, type=str, help="Specify the position prop bet is for")
    args = parser.parse_args()
    week = str(args.week)
    position = args.position

    ##### Get Yahoo Auth ####

    # Yahoo Keys
    with open('./oauth.json') as json_yahoo_file:
        auths = json.load(json_yahoo_file)
    yahoo_consumer_key = auths['consumer_key']
    yahoo_consumer_secret = auths['consumer_secret']
    yahoo_access_key = auths['access_token']
    #yahoo_access_secret = auths['access_token_secret']
    json_yahoo_file.close()

    global game_id, league_id, tid_list

    # League and GameID
    with open('./league_info.json') as json_league_file:
        configs = json.load(json_league_file)
    game_id = configs['game_id']
    league_id = configs['league_id']
    tid_list = configs['team_ids']
    sheet_id = configs['sheet_id']
    json_league_file.close()

    print(game_id, league_id)

    #### Declare Yahoo ##


    global yahoo_api
    yahoo_api = Yahoo_Api(yahoo_consumer_key, yahoo_consumer_secret, yahoo_access_key)#, yahoo_access_secret)

    # Getting all team information
    team_list = []
    for i in tid_list:
        team = get_team_info(i, week, position)
        team_list.append(team)


    # Updating a Google sheet to keep record
    scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('mfl-service-acct.json', scope)
    gs = gspread.authorize(credentials)

    gsheet = gs.open_by_key(sheet_id)
    worksheet = "Week%s%s" % (week, position)
    wsheet = gsheet.worksheet(worksheet)

    row_offset = 2

    for team in team_list:
        for i in range(row_offset, row_offset + len(team.prop_players)):
            if i == row_offset:
                wsheet.update_cell(i, 1, team.manager)
                wsheet.update_cell(i, 5, team.prop_total)
            wsheet.update_cell(i, 2, team.prop_players[row_offset-i]['name'])
            wsheet.update_cell(i, 3, team.prop_players[row_offset-i]['selected_position'])
            wsheet.update_cell(i, 4, team.prop_players[row_offset-i]['points'])
            i += 1
        row_offset += len(team.prop_players) + 2



if __name__ == "__main__":
    main()





import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from helper_functions import get_key

class HoldetScraper():
  def __init__(self):
    self.__active_games_dict, self.__inactive_games_dict = self.__get_active_games_dict()

    self.active_games = [*self.__active_games_dict]
    self.active_games.sort()
    
    self.inactive_games = [*self.__inactive_games_dict]
    self.inactive_games.sort()

  def __game_has_started(self, game_url: str) -> bool:
    """
    Check if a specific game on Holdet.dk has started
    Arguments:
        game (str): the name of a game on Holdet.dk
    Returns:
        An boolean indicating if the game has started
    """

    url = f'https://www.holdet.dk/da/{game_url}/leaderboards/praemiepuljen'
    html_raw = requests.get(url)
    soup = BeautifulSoup(html_raw.content, 'html.parser')
    rounds = soup.find_all(name = 'ul', id = 'rounds')
    has_started = len(rounds) > 0

    return has_started
  
  def __get__games_dict(self) -> dict:
    """
    Get a dictionary of games on Holdet.dk
    Arguments:
        None
    Returns:
        A dictionary with games as keys and game urls as values
    """

    url = 'https://www.holdet.dk/da'
    html_raw = requests.get(url)
    soup = BeautifulSoup(html_raw.content, 'html.parser')
    games = soup.find_all(name='div', id=re.compile('game'))

    game_dict = {}
    for g in games:
      game = g.find(name='h1').text
      game_url = g.find_all(name='a', href=True)[0]['href'].replace('/da/','')
      game_dict[game] = game_url

    return game_dict

  def __get_active_games_dict(self):
    """
    Get a dictionary of active games on Holdet.dk together with a dictionary of games that have been launched but have not yet started
    Arguments:
        None
    Returns:
        Two dictionaries with games as keys and game urls as values
    """
    games_dict = self.__get__games_dict()
    active = {}
    not_yet_started = {}

    for game, game_url in games_dict.items():
      if self.__game_has_started(game_url):
        active[game] = game_url
      else:
        not_yet_started[game] = game_url
    
    return active, not_yet_started


  def __get_lastest_round(self, game: str) -> int:
    """
    Get the latest round of a specific game on Holdet.dk
    Arguments:
        game (str): the name of an active game on Holdet.dk
    Returns:
        An integer representing the latest round of the game
    """

    game_url = self.__active_games_dict[game]
    url = f'https://www.holdet.dk/da/{game_url}/leaderboards/praemiepuljen'
    html_raw = requests.get(url)
    soup = BeautifulSoup(html_raw.content, 'html.parser')
    rounds = soup.find_all(name = 'ul', id = 'rounds')[0]
    latest_round = rounds.find_all(name = 'li', class_ = 'active')[0].text
    latest_round = int(re.findall(r'\d+', latest_round)[0])  

    return latest_round

  def __get_no_of_contestants(self, game: str) -> int:
    """
    Get the number of contestants in præmiepuljen for a specific game on Holdet.dk
    Arguments:
        game (str): the name of an active game on Holdet.dk
    Returns:
        An integer with the number of contestants in præmiepuljen for the game
    """
    
    game_url = self.__active_games_dict[game]
    url = f'https://www.holdet.dk/da/{game_url}/leaderboards/praemiepuljen'
    html_raw = requests.get(url)
    soup = BeautifulSoup(html_raw.content, 'html.parser')
    contestants = int(soup.find_all(name = 'div', class_ = 'panel summary')[0].find_all(name='h3')[0].text.replace('.',''))

    return contestants
  
  def __get_standings_table_page(self, game: str, round: int, page: int) -> pd.DataFrame:
    """
    Get data for the contestants in a specific page of the standings table (præmiepuljen) for a specific round of a specific game on Holdet.dk
    Arguments:
        game (str): the name of an active game on Holdet.dk
        round (int): the round of the game
        page (int): the page number of the standings table (præmiepuljen)
    Returns:
        A dataframe with data for the contestants in this standings table page of præmiepuljen
    """
    game_url = self.__active_games_dict[game]
    url = f'https://www.holdet.dk/da/{game_url}/leaderboards/praemiepuljen/{str(round)}/all/rank/asc/{str(page)}'
    html_raw = requests.get(url)
    soup = BeautifulSoup(html_raw.content, 'html.parser')
    table_html = soup.find_all(name = 'table')
    table_df = pd.read_html(str(table_html), thousands='.', decimal=',')[0][['#', 'Global', 'Spring', 'Hold', 'Manager', 'Afstand', 'Runde', 'Runde.1']]
    #%%
    teams = soup.find_all(name = 'table')[0].find_all('a', href=lambda href: href and '/userteams/' in href)
    table_df['HoldLink'] = [link.get('href') for link in teams]
    #%%
    # Exclude deleted managers
    table_df = table_df[table_df['Manager']!='<Slettet>']
    #%%
    managers = soup.find_all('a',href=lambda href: href and '/users/' in href, title=True)
    table_df['ManagerLink'] = [link.get('href') for link in managers]
    #%%
    table_df.rename(columns={'#': 'Præmiepulje', 
                                'Afstand': 'Værdi',
                                'Runde': 'Afstand',
                                'Runde.1': 'RundeVækst'}, inplace=True)
    table_df = table_df[['Præmiepulje', 'Global', 'Spring', 'Hold', 'HoldLink', 'Manager', 'ManagerLink', 'Værdi', 'Afstand', 'RundeVækst']]
    return table_df
  
  def get_standings_table(self, game: str, round = 0, top = 100) -> pd.DataFrame:
    """
    Get Top X of præmiepuljen of a specific round of a specific game on Holdet.dk
    Arguments:
        game (str): the name of an active game on Holdet.dk
        round (int): the round of the game. Defaults to the latest round
        top (int): the top part of præmiepuljen you want. Defaults to Top 100
    Returns:
        A dataframe with data for the Top X contestants in præmiepuljen for the specified game and round
    """

    if game not in self.active_games:
      raise ValueError('Det valgte spil er ikke aktivt. Vælg et spil fra active_games listen')

    latest_round = self.__get_lastest_round(game=game)
    contestants = self.__get_no_of_contestants(game=game)

    if round == 0: # if no round is specified, return results for latest round
      round = latest_round
    
    if round < 0:
      raise ValueError('Den første tilgængelige runde er Runde 1')
    elif round > latest_round:
      raise ValueError(f'Den sidste tilgængelige runde er Runde {str(latest_round)}')
    
    if top <= 0:
      raise ValueError('Kan ikke data for mindre end én deltager')
    elif top > contestants:
      print(f'Du har efterspurgt Top {str(top)}, men der findes kun {str(contestants)} deltagere i præmiepuljen. \n Returnerer hele præmiepuljen.')
      n_pages = contestants

    page_list = []
    page = 1 # init
    while True:
      page_df = self.__get_standings_table_page(game=game, round=round, page=page)
      page_list.append(page_df)

      if 25*page >= top:
        break
      else:
        page = page + 1

    total_df = pd.concat(page_list).reset_index(drop=True)
    total_df = total_df.drop_duplicates('HoldLink')
    total_df = total_df[0:top]
    total_df['Spil'] = game
    total_df['Runde'] = round

    return total_df  

  def __get_team(self, team_link: str) -> pd.DataFrame:
    """
    Get a specific team on Holdet.dk
    Arguments:
        team_link (str): the url of a team on Holdet.dk, without the 'www.holdet.dk' part
    Returns:
        A dataframe with data for the specified team
    """

    url = f'https://www.holdet.dk{team_link}'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    players = soup.find_all(name = 'tbody')[0].find_all(name = 'tr', class_ = re.compile('p'))
    
    team_list = []
    for p in players:
      captain_check = p.find(name='i', class_='icon-star large gold captain')
      if captain_check is not None:
        captain = True
      else:
        captain = False

      row = {
          'SpillerNavn': p['fs-player-name'],
          'SpillerHold': p['fs-player-team'],
          'SpillerPosition': p['fs-player-position'],
          'SpillerKaptajn': captain,
          'SpillerVærdi': int(p['value']),
          'SpillerVækst': int(p['growth'])
      }
      team_list.append(row)
    
    team = pd.DataFrame.from_records(team_list)

    game_url = team_link.split('/userteams/')[0].replace('/da/','')
    game = get_key(self.__active_games_dict, game_url)

    team['Spil'] = game
    team['Runde'] = self.__get_lastest_round(game=game)
    team['Hold'] = soup.find_all(name = 'div', id = 'fantasyteam-header')[0].find(name = 'h3').text
    team['Formation'] = str((team['SpillerPosition']=='Forsvar').sum()) + '-' + str((team['SpillerPosition']=='Midtbane').sum()) + '-' + str((team['SpillerPosition']=='Angreb').sum())
    team['Manager'] = soup.find_all(name = 'div', class_ = 'byline')[1].contents[3].text
    team['ManagerPoints'] = int(str(soup.find_all(name = 'div', class_ = 'byline')[1].contents[6]).strip().replace('.', ''))
    team['HoldLink'] = team_link

    team = team[['Spil', 'Runde', 'Hold', 'Formation', 'HoldLink', 'Manager', 'ManagerPoints', 
                 'SpillerNavn', 'SpillerHold', 'SpillerPosition', 'SpillerKaptajn', 'SpillerVærdi', 'SpillerVækst']]

    return team

  def get_teams(self, team_link_list: list) -> pd.DataFrame:
    """
    Get teams on Holdet.dk
    Warning: The teams returned will always be those of the currently active round
    Arguments:
        team_link_list (list): A list of team_links containing the url of a team on Holdet.dk, without the 'www.holdet.dk' part
    Returns:
        A dataframe with data for the specified teams
    """

    team_list = []
    for team_link in team_link_list:
      team_df = self.__get_team(team_link=team_link)
      team_list.append(team_df)

    teams_df = pd.concat(team_list).reset_index(drop=True)  
    return teams_df

  def get_table_and_teams(self, game: str, round = 0, top = 100):
    """
    Get Top X of præmiepuljen of a specific round of a specific game on Holdet.dk together with the teams of the currently active round
    Warning: The teams returned will always be those of the currently active round
    Arguments:
        game (str): the name of an active game on Holdet.dk
        round (int): the round of the game. Defaults to the latest round
        top (int): the top part of præmiepuljen you want. Defaults to Top 100
    Returns:
        Two dataframes, 
          one with data for the Top X contestants in præmiepuljen for the specified game and round, and
          one with data for the teams of the currently active round
    """

    table_simple = self.get_standings_table(game=game, round=round, top=top)
    teams_simple = self.get_teams(table_simple['HoldLink'])

    table_info = table_simple[['HoldLink', 'Præmiepulje', 'Global']]
    
    teams_info = teams_simple[teams_simple['SpillerKaptajn']][['HoldLink', 'ManagerPoints', 'SpillerNavn', 'SpillerVækst', 'Formation']]
    teams_info.rename(columns={'SpillerNavn': 'Kaptajn',
                             'SpillerVækst': 'KaptajnVækst'}, inplace=True)  

    table_enriched = table_simple.merge(teams_info, how = 'left', left_on = 'HoldLink', right_on = 'HoldLink')
    teams_enriched = teams_simple.merge(table_info, how = 'left', left_on = 'HoldLink', right_on = 'HoldLink')

    table_enriched = table_enriched[['Spil', 'Runde', 'Præmiepulje', 'Global', 'Spring', 'Hold', 'Manager', 'ManagerPoints',
                                     'Værdi', 'Afstand', 'RundeVækst', 'Kaptajn', 'KaptajnVækst', 'Formation']]

    teams_enriched = teams_enriched[['Spil', 'Runde', 'Præmiepulje', 'Global', 'Hold', 'Formation', 'Manager', 'ManagerPoints', 
                                     'SpillerNavn', 'SpillerHold', 'SpillerPosition', 'SpillerKaptajn', 'SpillerVærdi', 'SpillerVækst']]

    return table_enriched, teams_enriched

if __name__ == "__main__":
    scraper = HoldetScraper()
    table, teams = scraper.get_table_and_teams(scraper.active_games[0])
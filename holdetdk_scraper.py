import pandas as pd
import numpy as np
from tqdm import tqdm
import re
import requests
import os
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from getpass import getpass
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


  def __get_active_round(self, game: str) -> int:
    """
    Get the active round of a specific game on Holdet.dk
    Arguments:
        game (str): the name of an active game on Holdet.dk
    Returns:
        An integer representing the active round of the game
    """

    game_url = self.__active_games_dict[game]
    url = f'https://www.holdet.dk/da/{game_url}/leaderboards/praemiepuljen'
    html_raw = requests.get(url)
    soup = BeautifulSoup(html_raw.content, 'html.parser')
    rounds = soup.find_all(name = 'ul', id = 'rounds')[0]
    active_round = rounds.find_all(name = 'li', class_ = 'active')[0].text
    active_round = int(re.findall(r'\d+', active_round)[0])  

    return active_round

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

  def __get_no_of_pages(self, game: str) -> int:
    """
    Get the number of pages in præmiepuljen for a specific game on Holdet.dk
    Arguments:
        game (str): the name of an active game on Holdet.dk
    Returns:
        An integer with the number of pages in præmiepuljen for the game
    """
    
    game_url = self.__active_games_dict[game]
    url = f'https://www.holdet.dk/da/{game_url}/leaderboards/praemiepuljen'
    html_raw = requests.get(url)
    soup = BeautifulSoup(html_raw.content, 'html.parser')
    pages = soup.find_all(name = 'ul', class_ = 'pagination')[0].find_all(name='a')
    n_pages = int(pages[len(pages)-2].text)

    return n_pages

  def __get_game_from_team_link(self, team_link: str) -> str:
    """
    Get the game associated with a team on Holdet.dk
    Arguments:
        team_link (str): team_link from a team on Holdet.dk
    Returns:
        The name of the game assoicated with the team
    """
    for game, game_url in self.__active_games_dict.items():
      if game_url in team_link:
          g = game
          break
    return g

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
  
  def get_standings_table(self, game: str, round = 0, top = 100, random_sample = False) -> pd.DataFrame:
    """
    Get Top X of præmiepuljen of a specific round of a specific game on Holdet.dk
    Arguments:
        game (str): the name of an active game on Holdet.dk
        round (int): the round of the game. Defaults to the active round
        top (int): the top part of præmiepuljen you want. Defaults to Top 100. Set to 0 in order to return all.
        random_sample (bool): Set to True in order to get a random sample from præmiepuljen. The number of teams returned is the number specified in the 'top' parameter.

    Returns:
        A dataframe with data for the Top X contestants in præmiepuljen for the specified game and round
    """

    if game not in self.active_games:
      raise ValueError('Det valgte spil er ikke aktivt. Vælg et spil fra active_games listen')

    active_round = self.__get_active_round(game=game)
    contestants = self.__get_no_of_contestants(game=game)
    n_pages = self.__get_no_of_pages(game=game)

    if round == 0: # if no round is specified, return results for active round
      round = active_round
    
    if round < 0:
      raise ValueError('Den første tilgængelige runde er Runde 1')
    elif round > active_round:
      raise ValueError(f'Den sidste tilgængelige runde er Runde {str(active_round)}')
    
    if top < 0:
      raise ValueError('Kan ikke hente data for mindre end én deltager')
    elif top == 0:
      top = contestants
    elif top > contestants:
      print(f'Du har efterspurgt Top {str(top)}, men der findes kun {str(contestants)} deltagere i præmiepuljen. \n Returnerer hele præmiepuljen.')
      top = contestants

    if not random_sample:
      description = f'{game}, Runde {str(round)}: Henter tabel for Top {str(top)} i præmiepuljen'
      scrape_range = range(1, int(np.ceil(top/24))+1)
    else:
      description = f'{game}, Runde {str(round)}: Henter tabel for {str(top)} tilfældige hold i præmiepuljen'
      scrape_range = range(1, n_pages + 1)

    page_list = []
    for page in tqdm(scrape_range, desc = description):
      page_df = self.__get_standings_table_page(game=game, round=round, page=page)
      page_list.append(page_df)

    total_df = pd.concat(page_list).reset_index(drop=True)
    total_df = total_df.drop_duplicates('HoldLink')

    if len(total_df) < top:
      print(f'Der findes kun {str(len(total_df))} valide (ikke-slettede) hold i præmiepuljen. \n Returnerer alle disse.')
      top = len(total_df)
  

    total_df['Spil'] = game
    total_df['Runde'] = round

    if not random_sample:
      total_df = total_df[0:top]
    else:
      total_df = total_df.sample(n = top)

    total_df.sort_values(by=['Præmiepulje'], inplace=True)
    total_df = total_df.reset_index(drop=True)  

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
    team['Runde'] = self.__get_active_round(game=game)
    team['Hold'] = soup.find_all(name = 'div', id = 'fantasyteam-header')[0].find(name = 'h3').text
    team['Formation'] = str((team['SpillerPosition']=='Forsvar').sum()) + '-' + str((team['SpillerPosition']=='Midtbane').sum()) + '-' + str((team['SpillerPosition']=='Angreb').sum())
    team['Manager'] = soup.find_all(name = 'div', class_ = 'byline')[1].contents[3].text
    team['ManagerPoints'] = int(str(soup.find_all(name = 'div', class_ = 'byline')[1].contents[6]).strip().replace('.', ''))
    team['HoldLink'] = team_link

    team = team[['Spil', 'Runde', 'Hold', 'Formation', 'HoldLink', 'Manager', 'ManagerPoints', 
                 'SpillerNavn', 'SpillerHold', 'SpillerPosition', 'SpillerKaptajn', 'SpillerVærdi', 'SpillerVækst']]

    return team

  def get_teams_from_active_round(self, team_link_list: list) -> pd.DataFrame:
    """
    Get teams on Holdet.dk
    Warning: The teams returned will always be those of the currently active round!
    Arguments:
        team_link_list (list): A list of team_links containing the url of a team on Holdet.dk, without the 'www.holdet.dk' part
    Returns:
        A dataframe with data for the specified teams
    """

    team_list = []
    for team_link in tqdm(team_link_list, desc = f'Henter hold'):
      team_df = self.__get_team(team_link=team_link)
      team_list.append(team_df)

    teams_df = pd.concat(team_list).reset_index(drop=True)  
    return teams_df
  
  def __get_team_from_old_round(self, driver, team_link: str, round: int) -> pd.DataFrame:
    """
    Get a team on Holdet.dk from a round that is not active anymore
    Warning: You need a 'gold team' in the requested game for this to work and you are required to log in during the proces!
    Arguments:
        team_link (str): the url of a team on Holdet.dk, without the 'www.holdet.dk' part
        round (int): the round from which you want this team
    Returns:
        A dataframe with data for the specified team from the specified round
    """

    driver.get(f'https://www.holdet.dk{team_link}/rounds')

    if not '/rounds' in driver.current_url:
      raise ValueError('Du er logget ind med en bruger som ikke har et guldhold i det pågældende spil. Du kan derfor kun hente data fra den aktive runde!')

    game = self.__get_game_from_team_link(team_link=team_link)
    active_round = self.__get_active_round(game=game)

    runde_buttons = driver.find_elements(by = By.CLASS_NAME, value = "toggle.turn")
    for button in runde_buttons: # fold den aktive runde ind
        if button.text.lower() == f'runde {str(active_round)}':
            button.click()
            break

    for button in runde_buttons: # fold den efterspurgte runde ud
        if button.text.lower() == f'runde {str(round)}':
            button.click()
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    table_html = soup.find_all(name = 'table')
    table_df = pd.read_html(str(table_html), thousands='.', decimal=',')[0]
    table_df.rename(columns={'Unnamed: 0': 'SpillerNavn',
                            'Unnamed: 1': 'SpillerPosition',
                            'Vækst': 'SpillerVækst',
                            'Kaptajn': 'KaptajnVækst'}, inplace=True)
    table_df = table_df[['SpillerNavn', 'SpillerPosition', 'SpillerVækst', 'KaptajnVækst']] 
    mask = [f'Runde {i}' for i in range(1,50)]
    mask.append('Alle')
    table_df.query("SpillerNavn not in @mask", inplace=True)
    table_df['SpillerKaptajn'] = table_df['KaptajnVækst'].notna()
    table_df.drop('KaptajnVækst', axis = 1, inplace=True)
    table_df.reset_index(inplace=True)

    for idx, player in enumerate(table_df['SpillerNavn']):
        split = player.split(' ')
        position = split[len(split)-1].strip()
        player = player.replace(position , '').strip()
        table_df.at[idx,'SpillerNavn'] = player
        table_df.at[idx,'SpillerPosition'] = position
    
    table_df['Spil'] = game
    table_df['Runde'] = round
    table_df['Hold'] = soup.find_all(name = 'div', id = 'fantasyteam-header')[0].find(name = 'h3').text
    table_df['Formation'] = str((table_df['SpillerPosition']=='Forsvar').sum()) + '-' + str((table_df['SpillerPosition']=='Midtbane').sum()) + '-' + str((table_df['SpillerPosition']=='Angreb').sum())
    table_df['Manager'] = soup.find_all(name = 'div', class_ = 'byline')[1].contents[3].text
    table_df['ManagerPoints'] = int(str(soup.find_all(name = 'div', class_ = 'byline')[1].contents[6]).strip().replace('.', ''))
    table_df['HoldLink'] = team_link
    table_df['Formation'] = str((table_df['SpillerPosition']=='Forsvar').sum()) + '-' + str((table_df['SpillerPosition']=='Midtbane').sum()) + '-' + str((table_df['SpillerPosition']=='Angreb').sum())
    table_df['SpillerHold'] = 'DummyHold'
    table_df['SpillerVærdi'] = 0

    table_df = table_df[['Spil', 'Runde', 'Hold', 'Formation', 'HoldLink', 'Manager', 'ManagerPoints', 
                         'SpillerNavn', 'SpillerHold', 'SpillerPosition', 'SpillerKaptajn', 'SpillerVærdi', 'SpillerVækst']]

    return table_df

  def get_teams_from_old_round(self, team_link_list: list, round: int) -> pd.DataFrame:
    """
    Get teams on Holdet.dk from a round that is not active anymore
    Warning: You need a 'gold team' in the requested game for this to work and you are required to log in during the proces!
    Note: The values returned in the columns 'SpillerHold' and 'SpillerVærdi' are dummy values since these can't be found on the team page for old rounds!
    Arguments:
        team_link_list (list): A list of team_links containing the url of a team on Holdet.dk, without the 'www.holdet.dk' part
        round (int): the round from which you want these teams
    Returns:
        A dataframe with data for the specified teams from the specified round
    """

    game = self.__get_game_from_team_link(team_link=team_link_list[0])
    active_round = self.__get_active_round(game=game)

    if round < 0:
      raise ValueError('Den første tilgængelige runde er Runde 1')
    elif round > active_round:
      raise ValueError(f'Den sidste tilgængelige runde er Runde {str(active_round)}')

    chrome_driver_path = str(Path(__file__).parent / "Drivers" / "chromedriver")

    if not os.path.exists(chrome_driver_path):
      if not os.path.exists(chrome_driver_path + '.exe'):
        raise FileNotFoundError(f'Please download a chromedriver from https://sites.google.com/chromium.org/driver/ and place it under {chrome_driver_path.replace("/chromedriver","")} with the name "chromedriver"')

    driver = webdriver.Chrome(service=Service(chrome_driver_path))
    driver.maximize_window()

    url = 'https://www.holdet.dk/da'
    driver.get(url)

    # accept cookies
    cookie_buttons = driver.find_elements(by = By.CLASS_NAME, value = "CybotCookiebotDialogBodyButton")
    for button in cookie_buttons:
        if button.text.lower() == "tillad alle":
            button.click()
            break
    
    print('Log ind på Holdet.dk og tryk herefter ENTER')
    getpass('Log ind på Holdet.dk og tryk herefter ENTER')

    team_list = []
    for team_link in tqdm(team_link_list, desc = f'Henter hold'):
      team_df = self.__get_team_from_old_round(driver=driver, team_link=team_link, round = round)
      team_list.append(team_df)

    driver.quit()

    teams_df = pd.concat(team_list).reset_index(drop=True)  

    return teams_df

  def get_table_and_teams(self, game: str, round = 0, top = 100, random_sample = False, table_from_previous_round = False):
    """
    Get Top X of præmiepuljen of a specific round of a specific game on Holdet.dk together with the teams from that round
    Arguments:
        game (str): the name of an active game on Holdet.dk
        round (int): the round of the game. Defaults to the active round
        top (int): the top part of præmiepuljen you want. Defaults to Top 100
        random_sample (bool): Set to True in order to get a random sample from præmiepuljen. The number of teams returned is the number specified in the 'top' parameter.
        table_from_previous_round (bool): If you are scraping teams from the active round during a match it can be advantageous to set this parameter to True. The table returned will then be from the previous round and thus you eliminate the risk of the table shifting during runtime which could potentially cause inaccuraries/duplicates
    Returns:
        Two dataframes, 
          one with data for the Top X contestants in præmiepuljen for the specified game and round, and
          one with data for the teams of the specified round
    """
    
    active_round = self.__get_active_round(game=game)

    if round == 0:
      round = active_round

    if table_from_previous_round and round == active_round: # get table from previous round
      round = max(active_round - 1,1)

    table_simple = self.get_standings_table(game=game, round=round, top=top, random_sample=random_sample)

    if table_from_previous_round and round == max(active_round - 1,1): #get teams from the active round
      round = active_round

    if round == active_round:
      teams_simple = self.get_teams_from_active_round(team_link_list = table_simple['HoldLink'])
    elif round < active_round:
      teams_simple = self.get_teams_from_old_round(team_link_list = table_simple['HoldLink'], round=round)

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
  
  def __calc_popularity(self, teams_table: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate popularity percentages and captaincy popularity of the players in the teams_table
    Arguments:
        teams_table (pd.DataFrame): a Dataframe returned by one of the functions get_teams_from_active_round(), get_teams_from_old_round() or get_table_and_teams
    Returns:
        A DataFrame with popularity percentages and captaincy popularity for all players in the teams_table
    """

    n_teams = len(teams_table['Hold'].drop_duplicates())

    popularity = teams_table.groupby(['SpillerNavn', 'SpillerPosition']).size().reset_index(name='Antal')
    popularity['Pop%'] = (popularity['Antal']/n_teams)
    popularity.drop(['Antal'], axis = 1, inplace = True)

    captain = teams_table[teams_table['SpillerKaptajn']].groupby(['SpillerNavn', 'SpillerPosition']).size().reset_index(name='Antal')
    captain['(C)%'] = (captain['Antal']/n_teams)
    captain.drop(['Antal'], axis = 1, inplace = True)

    final = popularity.merge(captain, how = 'left', left_on = ['SpillerNavn','SpillerPosition'], right_on = ['SpillerNavn','SpillerPosition'])
    final['(C)%'] = final['(C)%'].fillna(0)
    final.sort_values(by=['Pop%', '(C)%'], inplace=True, ascending=False)

    return final

  def calc_popularity_table(self, teams_table: pd.DataFrame, splits = [100, 1000]) -> pd.DataFrame:
    """
    Calculate popularity percentages and captaincy popularity of the players in the teams_table
    Arguments:
        teams_table (pd.DataFrame): a Dataframe returned by one of the functions get_teams_from_active_round(), get_teams_from_old_round() or get_table_and_teams
        splits (list): The splits for which you want to calculate popularity
    Returns:
        A DataFrame with popularity percentages and captaincy popularity for all players in the teams_table
    """

    n_teams = len(teams_table['Hold'].drop_duplicates())

    samlet = self.__calc_popularity(teams_table=teams_table)
    samlet.rename(columns={'Pop%': 'Pop% (samlet)',
                           '(C)%': '(C)% (samlet)'}, inplace=True) 
    pop_table = samlet
    for split in splits:
      if n_teams < split:
        print(f'Der er kun {str(n_teams)} hold i tabellen. Returnerer alle meningsfulde splits.')
        break

      split_top = self.__calc_popularity(teams_table=teams_table[0:split])
      split_top.rename(columns={'Pop%': f'Pop% (Top {str(split)})',
                           '(C)%': f'(C)% (Top {str(split)})'}, inplace=True)
      pop_table = pop_table.merge(split_top, how = 'left', left_on = ['SpillerNavn','SpillerPosition'], right_on = ['SpillerNavn','SpillerPosition'])    
    
    pop_table.fillna(0, inplace=True)
    pop_table = pop_table.reset_index(drop=True)  

    return pop_table

if __name__ == "__main__":
    scraper = HoldetScraper()
    table, teams = scraper.get_table_and_teams(scraper.active_games[0])
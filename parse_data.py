import numpy as np
import pandas as pd
import requests 
import time
from bs4 import BeautifulSoup
from io import StringIO


'''
** Scraping the Data from the website www.basketball-reference.com **
Downlaoded them to avoid scraping the website continuously
'''

'''
NJN -> 2005 - 2012, BRK -> 2013-2025
CHA -> 2005 - 2014, CHO -> 2015 -> 2025
NOH -> 2005 - 2013, NOP -> 2014 -> 2025
SEA -> 2005 - 2008, OKC -> 2009 -> 2025

def get_accr(team,year):
    if team == 'BRK' and year <= 2012:
        return "NJN"
    elif team == 'CHO' and year <= 2014:
        return "CHA"
    elif team == 'NOP' and year <= 2013:
        if year == 2006 or year == 2007:
            return "NOK"
        return "NOH"
    elif team == 'OKC' and year <= 2008:
        return "SEA"
    else:
        return team

GETTING DATA ON COMPUTER
import time

teams = ['ATL','BOS','BRK','CHO','CHI','CLE','DAL','DEN','DET',
'GSW','HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK',
'OKC','ORL','PHI','PHO','POR','SAC','SAS','TOR','UTA','WAS']
range_years = list(range(2005,2026))
url_start = "https://www.basketball-reference.com/teams/{}/{}_games.html" #format w/ (team,year)

teams = ['NOP']

for t in teams:
    for year in range_years:
        team = get_accr(t,year)
        url = url_start.format(team,year)
        data = requests.get(url)
        with open("/Users/dakshprashar/Desktop/Project/{}/{}.html".format(t,year), "w+") as f:
            f.write(data.text)
    #time.sleep(120)
'''



'''
Functions used to format each team's df when it is parsed
'''

## Dictionary used to return a common abbreviation for each team
def get_team_abbreviation(full_name):
    nba_teams = {
        'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BRK', 'Charlotte Hornets': 'CHO',
        'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE', 'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN',
        'Detroit Pistons': 'DET', 'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
        'Los Angeles Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM', 'Vancouver Grizzlies': 'MEM', 'Miami Heat': 'MIA',
        'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN', 'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK',
        'Oklahoma City Thunder': 'OKC', 'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHO',
        'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS', 'Toronto Raptors': 'TOR',
        'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS', 
        'New Jersey Nets': 'BRK', 'New Orleans Hornets': 'NOP', 'Charlotte Bobcats': 'CHO', 'Seattle SuperSonics': 'OKC', 'New Orleans/Oklahoma City Hornets': 'NOP'
    }
    return nba_teams.get(full_name, None)

## Used to get the current streak value
def get_streak(streak):
    if not streak:
        return 0
    s = streak.split(' ')
    if s[0] == 'L':
        return int(s[1]) * -1
    return int(s[1])

## Main function that returns the df after it adds/removes the appropriate columns
def format_df(df):
    columns_to_keep = ["G", "Date", "Unnamed: 5", "Opponent", "Tm", "Opp", "W", "L", "Streak"]
    df = df[columns_to_keep]
    
    df = df[df["G"] != "G"].copy()

    df["Streak"] = df["Streak"].shift(1)
    df["W"] = df["W"].shift(1)
    df["L"] = df["L"].shift(1)

    numeric_cols = ["W", "L", "Tm", "Opp"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["Date"] = pd.to_datetime(df["Date"], format="%a, %b %d, %Y")
    df["Rest_days"] = df["Date"].diff().dt.days.fillna(120).astype(int)

    df["Streak"] = df["Streak"].apply(get_streak)
    df["Home_Game"] = np.where(df["Unnamed: 5"] == "@", 1, 0)
    df["Opponent"] = df["Opponent"].apply(get_team_abbreviation)
    df["First_Game"] = np.where(df["G"] == "1", 1, 0)

    df["Spread"] = df["Tm"] - df["Opp"]

    columns_to_drop = ["G","Unnamed: 5","Tm", "Opp"]
    df = df.drop(columns=columns_to_drop, errors='ignore')
    
    df.set_index("Date", inplace=True)
    
    return df



'''
Parsing the data for each team using the downloaded HTML files
'''

range_years = list(range(2005,2026))
df_dic = {}

teams = ['ATL','BOS','BRK','CHO','CHI','CLE','DAL','DEN','DET',
        'GSW','HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK',
        'OKC','ORL','PHI','PHO','POR','SAC','SAS','TOR','UTA','WAS']

for team in teams:
    dfs = []
    for year in range_years:
        with open("data_files/{}/{}.html".format(team,year)) as f:
            page = f.read()
        soup = BeautifulSoup(page, "html.parser")
        tbl = soup.find(id="games")
        df = pd.read_html(StringIO(str(tbl)))[0]
        df = df.loc[df["Unnamed: 4"].notna()] # Ensure only games that are played are recorded
        df = format_df(df)
        dfs.append(df)
    total_df = pd.concat(dfs)
    df_dic[team] = total_df



## Added Opponent Data to the df

def populate_opponent_data(df_dic):
    for k in df_dic:
        df = df_dic[k]
        for row in df.itertuples():
            opponent = row.Opponent
            if opponent in df_dic:
                df.at[row.Index, "Opp_W"] = df_dic[opponent].loc[row.Index,"W"]
                df.at[row.Index, "Opp_L"] = df_dic[opponent].loc[row.Index,"L"]
                df.at[row.Index, "Opp_Streak"] = df_dic[opponent].loc[row.Index,"Streak"]
                df.at[row.Index, "Opp_Rest_days"] = df_dic[opponent].loc[row.Index,"Rest_days"]

        df_dic[k] = df_dic[k].drop(columns=["Opponent"], errors='ignore')

populate_opponent_data(df_dic)

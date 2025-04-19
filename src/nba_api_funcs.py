from nba_api.stats.endpoints import playbyplay, teamgamelog, leaguegamelog
from nba_api.stats.static import teams
import requests
import streamlit as st

# https://github.com/swar/nba_api/issues/194#issuecomment-755798127
HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}
# proxy_host = "38.153.152.244"
# proxy_port = "9594"
# proxy_user = "vjndmcay"
# proxy_pass = "d7mpey8q2jwi"
# proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
proxy = ""
	
@st.cache_data
def get_nba_teams():
    nba_teams = teams.get_teams()
    team_options = {team['full_name']: (team['abbreviation'], team['id']) for team in nba_teams}
    return team_options

@st.cache_data
def get_recent_league_games(n_recent):
    try:
        log = leaguegamelog.LeagueGameLog(player_or_team_abbreviation='T', headers=HEADERS, proxy=proxy)
        df = log.get_data_frames()[0]
        df = df.sort_values('GAME_DATE', ascending=False)
        game_options = []
        for _, row in df.head(n_recent).iterrows():
            game_id = row['GAME_ID']
            matchup = row['MATCHUP']
            game_date = row['GAME_DATE']
            label = f"{matchup} ({game_date})"
            game_options.append((label, game_id))
        return game_options
    except Exception as e:
        st.error(f"Error getting recent league games: {e}")
        return []

@st.cache_data
def get_team_recent_games(team_id, n_recent):
    try:
        log = teamgamelog.TeamGameLog(team_id=team_id, headers=HEADERS, proxy=proxy)
        df = log.get_data_frames()[0]
        game_options = []
        for _, row in df.head(n_recent).iterrows():
            game_id = row['Game_ID']
            matchup = row['MATCHUP']
            game_date = row['GAME_DATE']
            label = f"{matchup} ({game_date})"
            game_options.append((label, game_id))
        return game_options
    except Exception as e:
        st.error(f"Error getting recent games for team ID {team_id}: {e}")
        return []

@st.cache_data    
def get_game_events(game_id):
    try:
        pbp = playbyplay.PlayByPlay(game_id=game_id, headers=HEADERS, proxy=proxy)
        df = pbp.get_data_frames()[0]
        event_options = []
        for _, row in df.iterrows():
            event_id = int(row['EVENTNUM'])
            period = int(row['PERIOD'])
            clock = row['PCTIMESTRING']
            description = row['HOMEDESCRIPTION'] or row['VISITORDESCRIPTION'] or row['NEUTRALDESCRIPTION']
            label = f"Q{period} - {clock} - {description}"
            event_options.append((label, event_id))
        return event_options
    except Exception as e:
        st.error(f"Error getting play-by-play for game {game_id}: {e}")
        return []

@st.cache_data
def get_video_event(game_id, event_id):
    url = f'https://stats.nba.com/stats/videoeventsasset?GameEventID={event_id}&GameID={game_id}'
    try:
        r = requests.get(url, headers=HEADERS, proxies=proxy)
        r.raise_for_status()
        data = r.json()
        if data['resultSets']['Meta']['videoUrls'] and data['resultSets']['playlist']:
            video_urls = data['resultSets']['Meta']['videoUrls']
            playlist = data['resultSets']['playlist']
            return {
                'video': video_urls[0]['lurl'],
                'desc': playlist[0]['dsc']
            }
        else:
            st.warning("No video found for this event.")
            return None
    except Exception as e:
        st.error(f"Error getting video for event {event_id}: {e}")
        return None

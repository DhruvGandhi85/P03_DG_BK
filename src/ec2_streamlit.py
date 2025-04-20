import streamlit as st
import json
import pandas as pd
import nba_api_funcs
import s3_uploader
import os
import mysql.connector
import plotly.express as px
from dotenv import load_dotenv

def load_DB_env_variables():
    load_dotenv()
    return {
        "RDS_HOST": os.getenv("RDS_DB_HOST"),
        "RDS_USER": os.getenv("RDS_USER"),
        "RDS_PASS": os.getenv("RDS_PASS"),
        "RDS_DB_NAME": os.getenv("RDS_DB_NAME"),
        "RDS_TABLE_NAME": os.getenv("RDS_TABLE_NAME"),
    }

def connect_to_db():
    env_vars = load_DB_env_variables()

    return mysql.connector.connect(host=env_vars["RDS_HOST"],
                                   user=env_vars["RDS_USER"],
                                   password=env_vars["RDS_PASS"],
                                   database=env_vars["RDS_DB_NAME"])

def fetch_nba_video_data():
    query = 'SELECT game_id, event_id, video, video_desc, notes FROM nba_video'
    conn = connect_to_db()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.set_page_config(page_title="ClipNotes - NBA Annotations", page_icon="🏀")
# , layout="wide"

page = st.sidebar.selectbox("Choose a page:", ["Home", "Community Posts", "Analytics"])

proxies = nba_api_funcs.load_proxy_env_variables()
proxy = proxies["http"]

if page == "Home":
        
    st.markdown("<h1 style='text-align: center; color: red; '>🏀 ClipNotes - NBA Annotations 🏀</h1>", unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: center; color: white; '>Select a Team (Optional)</h3>", unsafe_allow_html=True)
    team_options = nba_api_funcs.get_nba_teams()
    selected_team_name = st.selectbox("Choose a team to see their recent games (optional)", ["All Teams"] + list(team_options.keys()))

    st.markdown("<h3 style='text-align: center; color: white; '>Select a Game</h3>", unsafe_allow_html=True)
    n_recent = st.number_input("Number of Recent Games to Display", min_value=1, max_value=300, value=5, step=5)

    if selected_team_name == "All Teams":
        with st.spinner("Fetching recent games..."):
            game_list = nba_api_funcs.get_recent_league_games(n_recent, proxy)
    else:
        selected_team_abbreviation = team_options[selected_team_name]
        selected_team_id = selected_team_abbreviation[1]
        with st.spinner(f"Fetching recent games for {selected_team_name}..."):
            game_list = nba_api_funcs.get_team_recent_games(selected_team_id, n_recent, proxy)

    if game_list:
        game_labels = [label for label, gid in game_list]
        game_choice = st.selectbox("Choose a game", game_labels, index=0)

        if game_choice:
            game_id = dict(game_list)[game_choice]
            st.success(f"Selected Game ID: {game_id}")

            st.markdown("<h3 style='text-align: center; color: white; '>Select a Play</h3>", unsafe_allow_html=True)
            st.markdown("<h5 style='text-align: center; color: white; '>Note: Start of Periods do not have Video</h5>", unsafe_allow_html=True)
            with st.spinner(f"Fetching plays for game {game_id}..."):
                event_list = nba_api_funcs.get_game_events(game_id, proxy)

            if event_list:
                event_labels = [label for label, eid in event_list]
                event_choice = st.selectbox("Choose a Play", event_labels, index=0)

                if event_choice:
                    event_id = dict(event_list)[event_choice]
                    st.success(f"Selected Event ID: {event_id}")

                    st.markdown("<h2 style='text-align: center; color: white; '>Play Video and Notes</h2>", unsafe_allow_html=True)
                    video_event = nba_api_funcs.get_video_event(game_id, event_id, proxies)

                    if video_event:
                        st.video(video_event['video'])
                        st.markdown(f"<h5 style='text-align: center; color: white; '>Clip: {video_event['desc']}</h5>", unsafe_allow_html=True)

                        notes = st.text_area("Your Notes on this Play:")
                        if st.button("Save Notes"):
                            timestamp = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
                            
                            payload = {
                                "game_id": game_id,
                                "event_id": event_id,
                                "video": video_event['video'],
                                "desc": video_event['desc'],
                                "notes": notes}

                            with open(f"note_data_{timestamp}.json", "w") as f:
                                json.dump(payload, f)
                            
                            print(f"uploading note_data_{timestamp}.json to S3")
                            s3_uploader.main(f"note_data_{timestamp}.json")
                            os.remove(f"note_data_{timestamp}.json")

                            st.success("Notes uploaded.")
                            st.write("**Your Notes:**")
                            st.write(f"Game {game_id} - Event {event_id} - {video_event['desc']}")
                            st.write(f"Clip: {video_event['video']}")
                            st.write(notes)

                    else:
                        st.info("No video available for the selected play.")
            else:
                st.info("Could not fetch the list of plays for the selected game.")
    else:
        st.info("No recent games found.")
elif page == "Community Posts":
    st.markdown("<h1 style='text-align: center; color: red; '>🏀 Community Posts 🏀</h1>", unsafe_allow_html=True)
    df = fetch_nba_video_data()

    st.markdown("<h3 style='text-align: center; color: white; '>Select a Play</h3>", unsafe_allow_html=True)
    selected_notes = st.selectbox("Choose a play", df['notes'].tolist())
    selected_video_row = df[df['notes'] == selected_notes]
    selected_video_desc = selected_video_row['video_desc'].values[0]
    selected_video = selected_video_row['video'].values[0]
    selected_game_id = selected_video_row['game_id'].values[0]
    selected_event_id = selected_video_row['event_id'].values[0]
    st.video(selected_video)

    st.markdown(f"<h5 style='text-align: center; color: white; '>Clip: {selected_video_desc}</h5>", unsafe_allow_html=True)
    st.write(f"Game ID: {selected_game_id} - Event ID: {selected_event_id}")
    st.write("**Notes:**")
    st.write(selected_notes)

elif page == "Analytics":
    st.markdown("<h1 style='text-align: center; color: red; '>🏀 ClipNotes - NBA Annotations 🏀</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: white; '>Analytics Page</h3>", unsafe_allow_html=True)

    df = fetch_nba_video_data()

    if not df.empty:
        st.subheader("Distribution of Notes")
        notes_counts = df['notes'].apply(lambda x: len(x.split())).value_counts().sort_index()
        fig_notes = px.bar(notes_counts, x=notes_counts.index, y=notes_counts.values,
                             labels={'x': 'Number of Words in Note', 'y': 'Number of Notes'})
        st.plotly_chart(fig_notes)

        st.subheader("Number of Annotations per Game")
        game_counts = df['game_id'].value_counts().sort_values(ascending=False)
        fig_games = px.bar(game_counts, x=game_counts.index.astype(str), y=game_counts.values,
                             labels={'x': 'Game ID', 'y': 'Number of Annotations'})
        st.plotly_chart(fig_games)
    else:
        st.info("No annotation data available to display analytics.")
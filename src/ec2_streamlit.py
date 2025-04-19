import streamlit as st
import json
import pandas as pd
import nba_api_funcs
import s3_uploader
import os



st.set_page_config(page_title="ClipNotes - NBA Annotations", page_icon="🏀")
# , layout="wide"
st.markdown("<h1 style='text-align: center; color: red; '>🏀 ClipNotes - NBA Annotations 🏀</h1>", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: white; '>Select a Team (Optional)</h3>", unsafe_allow_html=True)
team_options = nba_api_funcs.get_nba_teams()
selected_team_name = st.selectbox("Choose a team to see their recent games (optional)", ["All Teams"] + list(team_options.keys()))

st.markdown("<h3 style='text-align: center; color: white; '>Select a Game</h3>", unsafe_allow_html=True)
n_recent = st.number_input("Number of Recent Games to Display", min_value=1, max_value=300, value=5, step=5)

if selected_team_name == "All Teams":
    with st.spinner("Fetching recent games..."):
        game_list = nba_api_funcs.get_recent_league_games(n_recent)
else:
    selected_team_abbreviation = team_options[selected_team_name]
    selected_team_id = selected_team_abbreviation[1]
    with st.spinner(f"Fetching recent games for {selected_team_name}..."):
        game_list = nba_api_funcs.get_team_recent_games(selected_team_id, n_recent)

if game_list:
    game_labels = [label for label, gid in game_list]
    game_choice = st.selectbox("Choose a game", game_labels, index=0)

    if game_choice:
        game_id = dict(game_list)[game_choice]
        st.success(f"Selected Game ID: {game_id}")

        st.markdown("<h3 style='text-align: center; color: white; '>Select a Play</h3>", unsafe_allow_html=True)
        st.markdown("<h5 style='text-align: center; color: white; '>Note: Start of Periods do not have Video</h5>", unsafe_allow_html=True)
        with st.spinner(f"Fetching plays for game {game_id}..."):
            event_list = nba_api_funcs.get_game_events(game_id)

        if event_list:
            event_labels = [label for label, eid in event_list]
            event_choice = st.selectbox("Choose a Play", event_labels, index=0)

            if event_choice:
                event_id = dict(event_list)[event_choice]
                st.success(f"Selected Event ID: {event_id}")

                st.markdown("<h2 style='text-align: center; color: white; '>Play Video and Notes</h2>", unsafe_allow_html=True)
                video_event = nba_api_funcs.get_video_event(game_id, event_id)

                if video_event:
                    st.video(video_event['video'])
                    st.markdown(f"<h5 style='text-align: center; color: white; '>Clip: {video_event['desc']}</h5>", unsafe_allow_html=True)

                    notes = st.text_area("Your Notes on this Play:")
                    if st.button("Save Notes"):
                        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        payload = {
                            "game_id": game_id,
                            "event_id": event_id,
                            "video": video_event['video'],
                            "desc": video_event['desc'],
                            "notes": notes
                        }

                        with open(f"note_data_{timestamp}.json", "w") as f:
                            json.dump(payload, f)
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
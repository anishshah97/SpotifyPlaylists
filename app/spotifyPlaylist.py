import streamlit as st

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
scope = "user-top-read%20user-read-currently-playing%20user-read-playback-state%20playlist-read-collaborative%20playlist-read-private%20user-library-read%20user-read-recently-played%20user-follow-read"

auth_manager = SpotifyOAuth(scope=scope, show_dialog=True)
auth_url = auth_manager.get_authorize_url()

link = f'[Sign into Spotify]({auth_url})'
st.markdown(link, unsafe_allow_html=True)
#sp = Spotify(auth_manager=auth_manager)

# def get_saved_tracks(page):
#     #Force 1 second sleep
#     time.sleep(1)
#     return sp.current_user_saved_tracks(limit=50, offset=page*50)['items']

# all_results = []
# results = sp.current_user_saved_tracks(limit=50)
# total_results = results['total']
# total_pages = math.ceil(total_results/50)
# all_tracks = list(chain.from_iterable([get_saved_tracks(page) for page in tqdm(list(range(total_pages)))]))

st.title('Hello World!')

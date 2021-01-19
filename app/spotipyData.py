import os
import uuid
from dotenv import load_dotenv, find_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import SessionState as session
import hashlib
load_dotenv(find_dotenv())

caches_folder = '.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

session_state = session.get(uuid=None, spotipy=None, data_path=None, data=None)
if not session_state.uuid:
    session_state.uuid = uuid.uuid4()

def session_cache_path():
    return caches_folder + session.uuid

def generateSpotifyObject():
    scope = "user-top-read%20user-read-currently-playing%20user-read-playback-state%20playlist-read-collaborative%20playlist-read-private%20user-library-read%20user-read-recently-played%20user-follow-read"
    auth_manager = SpotifyOAuth(scope=scope,
                                cache_path=session_cache_path(), 
                                show_dialog=True)

    # if request.args.get("code"):
    #     # Step 3. Being redirected from Spotify auth page
    #     auth_manager.get_access_token(request.args.get("code"))
    #     return redirect('/')

    # if not auth_manager.get_cached_token():
    #     # Step 2. Display sign in link when no token
    #     auth_url = auth_manager.get_authorize_url()
    #     return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 4. Signed in, display data
    sp = Spotify(auth_manager=auth_manager)
    return sp

def populateStateData():
    if not session_state.spotipy:
        session_state.spotipy = generateSpotifyObject()
    
    if not session_state.data_path:
        hashed_session_user_spotify_id = hashlib.sha256(session_state.spotipy['id']).hexdigest()
        session_state.data_path = f"s3://{hashed_session_user_spotify_id}.csv"

    if not session_state.data:
        #Try pulling data from data path
        #If success, pull data from s3 and store into session state and cache or some shit?
        #If fail, generate data, upload to s3 into data path and then store data into session state
        session_state.data = 

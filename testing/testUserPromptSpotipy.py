import spotipy
import spotipy.util as util

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

while True:
    username = input("Type the Spotify user ID to use: ")
    token = util.prompt_for_user_token(username, show_dialog=True)
    sp = spotipy.Spotify(token)
    pprint(sp.me())

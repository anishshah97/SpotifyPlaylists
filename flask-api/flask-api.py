import time
from flask import Flask
from flask_cors import CORS, cross_origin
import spotipy
from flask import request
from utils import spotifyUser

app = Flask(__name__)
CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


def get_my_spotify(spotify_token):
    spotify = spotipy.Spotify(auth=spotify_token)
    return spotifyUser(spotify)


@app.route("/my_spotify_id", methods=["POST"])
@cross_origin()
def get_my_spotify_id():

    body = request.get_json()
    my_spotify = get_my_spotify(body["spotify_token"])
    return {"spotifyName": my_spotify.spotify_me["display_name"]}


@app.route("/my_spotify_liked", methods=["POST"])
@cross_origin()
def get_my_spotify_liked():

    body = request.get_json()
    my_spotify = get_my_spotify(body["spotify_token"])
    my_spotify.set_users_liked_song_info()
    return {"data": my_spotify.liked_songs_info["liked_tracks"].head().to_json()}


@app.route("/time")
def get_current_time():
    return {"time": time.time()}


if __name__ == "__main__":
    app.run(debug=True)

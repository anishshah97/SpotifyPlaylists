import time

import spotipy
from flask import Flask, request
from flask_cors import CORS, cross_origin

from utils import spotifyUserSession

app = Flask(__name__)
CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


def get_my_spotify(spotify_token):
    spotify = spotipy.Spotify(auth=spotify_token)
    return spotifyUserSession(spotify)


@app.route("/", methods=["GET"])
@cross_origin()
def hello():
    return {"hello": "world"}


@app.route("/my_spotify_id", methods=["POST"])
@cross_origin()
def get_my_spotify_id():

    body = request.get_json()
    my_spotify = get_my_spotify(body["spotify_token"])
    return {"spotifyName": my_spotify._spotify_user_profile["display_name"]}


@app.route("/my_spotify_liked", methods=["POST"])
@cross_origin()
def get_my_spotify_liked():

    body = request.get_json()
    my_spotify = get_my_spotify(body["spotify_token"])
    my_spotify.set_session_data(my_spotify.bulk_get_session_data())
    return {"data": my_spotify._info_dfs["liked_tracks"].head().to_json()}


@app.route("/time")
def get_current_time():
    return {"time": time.time()}


if __name__ == "__main__":
    app.run(debug=True)

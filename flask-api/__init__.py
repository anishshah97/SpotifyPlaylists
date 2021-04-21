import time
from flask import Flask
from flask_cors import CORS, cross_origin
import spotipy
from flask import request
from .utils import gather_all_data

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


def get_spotify_conn(spotify_token):
    return spotipy.Spotify(auth=spotify_token)


@app.route("/my_spotify", methods=["POST"])
@cross_origin()
def get_my_spotify():

    body = request.get_json()
    spotify = get_spotify_conn(body['spotify_token'])
    my_spotify = spotify.me()
    return {"spotifyName": my_spotify["display_name"]}


@app.route("/my_spotify_liked", methods=["POST"])
@cross_origin()
def get_my_spotify_liked():

    body = request.get_json()
    spotify = get_spotify_conn(body['spotify_token'])
    my_spotify_liked = gather_all_data(spotify)
    return {"data": my_spotify_liked.to_json()}


@app.route('/time')
def get_current_time():
    return {'time': time.time()}


if __name__ == "__main__":
    app.run(debug=True)

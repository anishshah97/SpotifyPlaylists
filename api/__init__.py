import time
from flask import Flask
from flask_cors import CORS, cross_origin
import spotipy
from flask import request

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


def get_spotify_conn(spotify_token):
    return spotipy.Spotify(auth=spotify_token)


@app.route("/spotify_me", methods=["POST"])
@cross_origin()
def get_me():

    body = request.get_json()
    spotify = get_spotify_conn(body['spotify_token'])
    spotify_me = spotify.me()
    return {"spotifyName": spotify_me["display_name"]}


@app.route('/time')
def get_current_time():
    return {'time': time.time()}


if __name__ == "__main__":
    app.run(debug=True)

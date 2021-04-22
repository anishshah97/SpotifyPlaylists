import argparse
import spotipy
from utils import str2bool
from spotifyClasses import spotifyUser

parser = argparse.ArgumentParser(description="CLI tool to drive spotify data gathering commands")
parser.add_argument(
    "-t",
    type=str2bool,
    dest="testing",
    nargs="?",
    const=True,
    default=False,
    help="Pull data from filesystem for downstream data tasks",
)
parser.add_argument(
    "-s",
    type=str2bool,
    dest="store",
    nargs="?",
    const=True,
    default=False,
    help="Store data to decided filesystem",
)
parser.add_argument(
    "-l",
    type=str2bool,
    dest="local",
    nargs="?",
    const=True,
    default=False,
    help="Use local routes for filesystem storage or data retrieval",
)
if __name__ == "__main__":
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope="user-top-read%20user-read-currently-playing%20user-read-playback-state%20playlist-read-collaborative%20playlist-read-private%20user-library-read%20user-read-recently-played%20user-follow-read",
        show_dialog=True,
    )
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    args = parser.parse_args()
    spot_user = spotifyUser(spotify, **vars(args))
    spot_user.set_users_liked_song_info()
    print(spot_user.export_liked_songs())
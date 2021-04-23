import argparse
import spotipy
from utils import spotifyUser

parser = argparse.ArgumentParser(description="CLI tool to drive spotify data gathering commands")
parser.add_argument(
    "-cd",
    "--cached-data",
    type=str,
    choices=["local", "s3"],
    dest="cached_data",
    default=None,
    help="String choice of where to get latest cache data from `local` or `s3`",
)
parser.add_argument(
    "-s",
    "--store",
    type=str,
    choices=["local", "s3"],
    dest="store",
    default=None,
    help="String choice of whether to store in `local` or `s3`",
)
if __name__ == "__main__":
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope="user-top-read%20user-read-currently-playing%20user-read-playback-state%20playlist-read-collaborative%20playlist-read-private%20user-library-read%20user-read-recently-played%20user-follow-read",
        show_dialog=True,
    )
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    args = parser.parse_args()
    # TODO: Abstract spotifyUser testing into another class that wraps the spotifyUSer class which holds only necessary information
    spot_user = spotifyUser(spotify, **vars(args))
    spot_user.set_users_liked_song_info()
    print(spot_user.export_liked_songs())

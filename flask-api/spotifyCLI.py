import argparse
import spotipy
from utils import spotifyUser

parser = argparse.ArgumentParser(description="CLI tool to drive spotify data gathering commands")
parser.add_argument(
    "-td",
    "--test-data",
    type=str,
    choices=["local", "s3"],
    default=None,
    help="String choice of job board for which to search and scrape from",
)
parser.add_argument(
    "-s",
    "--store",
    type=str,
    choices=["local", "s3"],
    default=None,
    help="String choice of job board for which to search and scrape from",
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

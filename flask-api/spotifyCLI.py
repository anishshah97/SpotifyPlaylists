import argparse

import spotipy

from utils import spotifyUserSession

parser = argparse.ArgumentParser(
    description="CLI tool to drive spotify data gathering commands"
)
parser.add_argument(
    "-ods",
    "--origin-data-source",
    type=str,
    choices=["local", "s3", "redis", "mongo"],
    dest="origin_data_source",
    default=None,
    help="String choice of where to get latest cache data from `local`, `s3`, `redis`, or `mongo`",
)
parser.add_argument(
    "-eds",
    "--export-data-source",
    type=str,
    choices=["local", "s3", "redis", "mongo"],
    dest="export_data_source",
    default=None,
    help="String choice of whether to store in `local`, `s3`, `redis`, or `mongo`",
)


def main(args):
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope="user-top-read%20user-read-currently-playing%20user-read-playback-state%20playlist-read-collaborative%20playlist-read-private%20user-library-read%20user-read-recently-played%20user-follow-read",
        show_dialog=True,
    )
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    # TODO: Abstract spotifyUser testing into another class that wraps the spotifyUSer class which holds only necessary information
    spot_user = spotifyUserSession(spotify, **vars(args))
    liked_track_dicts = spot_user.get_and_update_user_liked_tracks_data()
    liked_tracks = liked_track_dicts["liked_tracks"]
    print(f"liked_tracks.shape:{liked_tracks.shape}")
    liked_track_features = liked_track_dicts["liked_track_features"]
    print(f"liked_track_features.shape:{liked_track_features.shape}")
    liked_track_artist_features = liked_track_dicts["liked_track_artist_features"]
    print(f"liked_track_artist_features.shape:{liked_track_artist_features.shape}")

    # spot_user.set_session_data(spot_user.bulk_get_session_data())
    # spot_user.bulk_store_session_data()


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)

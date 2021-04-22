from utils import chunk, str2bool
import pandas as pd
import flatdict
import spotipy
from dotenv import load_dotenv, find_dotenv
import os
import math
from itertools import chain
import time
from tqdm import tqdm
from pathlib import Path
from datetime import datetime

load_dotenv(find_dotenv())
date_format_string = "%m-%d-%Y-%H-%M-%S"


def get_saved_track_page_count(spotify):
    first_page_saved_tracks = spotify.current_user_saved_tracks(limit=50)
    # Tells total amount of saved tracks
    count_saved_songs = first_page_saved_tracks["total"]
    total_pages_saved_songs = math.ceil(count_saved_songs / 50)  # Can get 50 tracks at a time
    return total_pages_saved_songs


def get_saved_tracks(spotify, page_num):
    time.sleep(0.1)
    return spotify.current_user_saved_tracks(limit=50, offset=page_num * 50)["items"]


def get_track_features(spotify, track_ids):
    time.sleep(0.1)
    if len(track_ids) > 100:
        print("Too many tracks")
    else:
        return spotify.audio_features(track_ids)


def get_artist_features(spotify, artist_ids):
    time.sleep(0.1)
    if len(artist_ids) > 50:
        print("Too many tracks")
    else:
        return spotify.artists(artist_ids)


def flatten_artist_features(artist_features):

    artist_follower_total = artist_features.get("followers", {}).get("total")
    artist_genres = artist_features.get("genres", [])
    artist_spid = artist_features.get("id")
    artist_img_urls = artist_features.get("images", [{"url": None}])
    if len(artist_img_urls) == 0:
        artist_img_url = None
    else:
        artist_img_url = artist_img_urls[0].get("url")
    artist_popularity = artist_features.get("popularity")

    flattened_artist_features = {
        "artist_follower_total": artist_follower_total,
        "artist_genres": artist_genres,
        "artist_spid": artist_spid,
        "artist_img_url": artist_img_url,
        "artist_popularity": artist_popularity,
    }

    return flattened_artist_features


def get_liked_tracks_df(spotify):
    total_pages_saved_songs = get_saved_track_page_count(spotify)
    liked_tracks = list(
        chain.from_iterable(
            [
                get_saved_tracks(spotify, page_num)
                for page_num in tqdm(list(range(total_pages_saved_songs)))
            ]
        )
    )
    flattened_liked_tracks = [dict(flatdict.FlatterDict(track)) for track in liked_tracks]
    full_liked_tracks_df = pd.DataFrame(flattened_liked_tracks)
    track_col_renames = {
        "track:album:album_type": "album_type",
        "track:album:artists:0:external_urls:spotify": "album_artist_spurl",
        "track:album:artists:0:id": "album_artist_spid",
        "track:album:artists:0:name": "album_artist_name",
        "track:album:artists:0:type": "album_artist_type",
        "track:album:external_urls:spotify": "album_spurl",
        "track:album:id": "album_spid",
        "track:album:images:0:url": "album_img_url",
        "track:album:name": "album_name",
        "track:album:release_date": "album_release_date",
        "track:album:total_tracks": "album_tracks_count",
        "track:album:type": "album_track_type",
        "track:artists:0:external_urls:spotify": "artist_spurl",
        "track:artists:0:id": "artist_spid",
        "track:artists:0:name": "artist_name",
        "track:artists:0:type": "artist_type",
        #    "track:duration_ms": "track_duration_ms",
        "track:explicit": "track_explicit",
        "track:external_ids:isrc": "track_isrc",
        "track:external_urls:spotify": "track_spurl",
        "track:id": "track_spid",
        "track:is_local": "track_is_local",
        "track:name": "track_name",
        "track:popularity": "track_popularity",
        "track:preview_url": "track_preview_url",
        "track:track_number": "track_number",
        "track:type": "track_type",
    }
    des_tracks_cols = ["added_at"] + list(track_col_renames.values())
    liked_tracks_df = full_liked_tracks_df.rename(track_col_renames, axis=1)[des_tracks_cols]
    return liked_tracks_df


def get_track_features_df(spotify, track_ids):

    chunked_track_ids = chunk(track_ids, 100)
    chunked_track_features = [
        get_track_features(spotify, chunked_tracks) for chunked_tracks in tqdm(chunked_track_ids)
    ]
    track_features = [val for val in list(chain.from_iterable(chunked_track_features)) if val]
    track_features_df = (
        pd.DataFrame(track_features)
        .drop(["uri", "track_href", "analysis_url", "type"], axis=1)
        .rename({"id": "spid"}, axis=1)
        .add_prefix("track_")
    )
    return track_features_df


def get_artist_features_df(spotify, artist_ids):
    chunked_artist_ids = chunk(artist_ids, 50)
    chunked_artist_features = [
        get_artist_features(spotify, chunked_artists)["artists"]
        for chunked_artists in tqdm(chunked_artist_ids)
    ]
    artist_features = [val for val in list(chain.from_iterable(chunked_artist_features)) if val]
    flattened_artist_features = [flatten_artist_features(artist) for artist in artist_features]
    artist_features_df = pd.DataFrame(flattened_artist_features)
    return artist_features_df


def gather_liked_tracks_data(spotify):

    liked_tracks_df = get_liked_tracks_df(spotify)
    liked_artist_ids = liked_tracks_df["artist_spid"].unique().tolist()
    liked_track_ids = liked_tracks_df["track_spid"].unique().tolist()

    liked_track_features_df = get_track_features_df(spotify, liked_track_ids)
    liked_artist_features_df = get_artist_features_df(spotify, liked_artist_ids)

    liked_songs_info_df = (
        pd.merge(liked_tracks_df, liked_track_features_df, on="track_spid")
        .merge(liked_artist_features_df, on="artist_spid")
        .sort_values("added_at", ascending=False)
    )
    liked_songs_info_df["interaction_style"] = "Liked Songs"

    print(liked_songs_info_df.shape)
    return liked_songs_info_df


def pull_liked_songs_data(spotify, testing=False):
    if testing:
        print("testing")
        user_id = spotify.me()["id"]
        data_dir = Path(Path().resolve().parent.parent, "data")
        file_path = Path(data_dir, user_id)
        file_path.mkdir(parents=True, exist_ok=True)
        user_file_paths = {
            data_path: datetime.strptime(data_path.name[:-4], date_format_string)
            for data_path in file_path.glob("*.csv")
        }
        latest_file = max(user_file_paths, key=user_file_paths.get)
        spotify_data_path = Path(file_path, latest_file)
        print(f"opening {spotify_data_path}")
        liked_songs_info_df = pd.read_csv(spotify_data_path)
    else:
        print("pulling")
        liked_songs_info_df = gather_liked_tracks_data(spotify)
    return liked_songs_info_df


def decide_path(spotify, local):
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
    user_id = spotify.me()["id"]
    now = datetime.now()  # current date and time
    date_time = now.strftime(date_format_string)
    file_name = f"{date_time}.csv"
    if local:
        data_dir = Path(Path().resolve().parent.parent, "data")
        file_path = Path(data_dir, user_id)
        file_path.mkdir(parents=True, exist_ok=True)
        spotify_data_path = Path(file_path, file_name)
    else:
        file_path = f"{user_id}/{file_name}"
        spotify_data_path = f"s3://{AWS_S3_BUCKET}/{file_path}"
    return spotify_data_path


def decide_storage_and_path(spotify, liked_songs_info_df, store=False, local=False):

    if store:
        spotify_data_path = decide_path(spotify, local)
        print(f"storing to {spotify_data_path}")
        if local:
            liked_songs_info_df.to_csv(spotify_data_path, index=False)
        else:
            AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
            AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
            liked_songs_info_df.to_csv(
                spotify_data_path,
                index=False,
                storage_options={"key": AWS_ACCESS_KEY_ID, "secret": AWS_SECRET_ACCESS_KEY},
            )


def main(spotify, testing=False, store=True, local=True):

    liked_songs_info_df = pull_liked_songs_data(spotify, testing)
    decide_storage_and_path(spotify, liked_songs_info_df, store, local)

    return liked_songs_info_df


import argparse

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
    print(main(spotify, **vars(args)))

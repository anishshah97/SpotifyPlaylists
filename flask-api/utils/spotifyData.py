import datetime
import math
import time
from itertools import chain

import flatdict
import pandas as pd
from tqdm import tqdm

from .utils import chunk


def get_saved_track_page_count(spotify):
    first_page_saved_tracks = spotify.current_user_saved_tracks(limit=50)
    # Tells total amount of saved tracks
    count_saved_songs = first_page_saved_tracks["total"]
    total_pages_saved_songs = math.ceil(
        count_saved_songs / 50
    )  # Can get 50 tracks at a time
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
    flattened_liked_tracks = [
        dict(flatdict.FlatterDict(track)) for track in liked_tracks
    ]
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
        "track:duration_ms": "track_duration_ms",
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
    liked_tracks_df = full_liked_tracks_df.rename(track_col_renames, axis=1)[
        des_tracks_cols
    ]
    liked_tracks_df["interaction_style"] = "Liked Songs"
    liked_tracks_df["time_pulled"] = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()
    return liked_tracks_df


def get_track_features_df(spotify, track_ids):

    chunked_track_ids = chunk(track_ids, 100)
    chunked_track_features = [
        get_track_features(spotify, chunked_tracks)
        for chunked_tracks in tqdm(chunked_track_ids)
    ]
    track_features = [
        val for val in list(chain.from_iterable(chunked_track_features)) if val
    ]
    track_features_df = (
        pd.DataFrame(track_features)
        .drop(["uri", "track_href", "analysis_url", "type"], axis=1)
        .rename({"id": "spid"}, axis=1)
        .add_prefix("track_")
        # .set_index("track_spid")
    )
    track_features_df["time_pulled"] = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()
    return track_features_df


def get_artist_features_df(spotify, artist_ids):
    chunked_artist_ids = chunk(artist_ids, 50)
    chunked_artist_features = [
        get_artist_features(spotify, chunked_artists)["artists"]
        for chunked_artists in tqdm(chunked_artist_ids)
    ]
    artist_features = [
        val for val in list(chain.from_iterable(chunked_artist_features)) if val
    ]
    flattened_artist_features = [
        flatten_artist_features(artist) for artist in artist_features
    ]
    artist_features_df = pd.DataFrame(
        flattened_artist_features
    )  # .set_index("artist_spid")
    artist_features_df["artist_genres"] = artist_features_df["artist_genres"].map(list)
    artist_features_df["time_pulled"] = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()
    return artist_features_df


def gather_liked_tracks_data(spotify):

    liked_tracks_df = get_liked_tracks_df(spotify)
    liked_artist_ids = liked_tracks_df["artist_spid"].unique().tolist()
    liked_track_ids = liked_tracks_df["track_spid"].unique().tolist()

    liked_track_features_df = get_track_features_df(spotify, liked_track_ids)
    liked_artist_features_df = get_artist_features_df(spotify, liked_artist_ids)

    liked_songs_info_dfs = {
        "liked_tracks": liked_tracks_df,
        "liked_track_features": liked_track_features_df,
        "liked_track_artist_features": liked_artist_features_df,
    }
    time_pulled = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for df in liked_songs_info_dfs.values():
        df["time_pulled"] = time_pulled

    return liked_songs_info_dfs

from .utils import chunk
import pandas as pd
import flatdict
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv, find_dotenv
import os
import math
from itertools import chain
import time
from tqdm import tqdm
from pathlib import Path


def get_saved_track_page_count(spotify):
    first_page_saved_tracks = spotify.current_user_saved_tracks(limit=50)
    # Tells total amount of saved tracks
    count_saved_songs = first_page_saved_tracks['total']
    total_pages_saved_songs = math.ceil(
        count_saved_songs/50)  # Can get 50 tracks at a time
    return total_pages_saved_songs


def get_saved_tracks(spotify, page_num):
    time.sleep(0.25)
    return spotify.current_user_saved_tracks(limit=50, offset=page_num*50)['items']


def get_track_features(spotify, track_ids):
    time.sleep(0.25)
    if len(track_ids) > 100:
        print("Too many tracks")
    else:
        return spotify.audio_features(track_ids)


def get_artist_features(spotify, artist_ids):
    time.sleep(0.25)
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
        "artist_popularity": artist_popularity
    }

    return flattened_artist_features


def gather_all_data(spotify):

    total_pages_saved_songs = get_saved_track_page_count(spotify)
    liked_tracks = list(chain.from_iterable([get_saved_tracks(
        spotify, page_num) for page_num in tqdm(list(range(total_pages_saved_songs)))]))
    flattened_liked_tracks = [dict(flatdict.FlatterDict(track))
                              for track in liked_tracks]
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
        "track:type": "track_type"
    }
    des_tracks_cols = [
        "added_at"
    ] + list(track_col_renames.values())
    liked_tracks_df = full_liked_tracks_df.rename(
        track_col_renames, axis=1)[des_tracks_cols]

    liked_track_ids = liked_tracks_df["track_spid"].unique().tolist()
    chunked_liked_track_ids = chunk(liked_track_ids, 100)
    chunked_liked_track_features = [get_track_features(
        spotify, chunked_tracks) for chunked_tracks in tqdm(chunked_liked_track_ids)]
    liked_track_features = [val for val in list(
        chain.from_iterable(chunked_liked_track_features)) if val]
    liked_track_features_df = pd.DataFrame(liked_track_features).drop([
        "uri",
        "track_href",
        "analysis_url",
        "type"
    ], axis=1).rename({"id": "spid"}, axis=1).add_prefix("track_")

    liked_artist_ids = liked_tracks_df["artist_spid"].unique().tolist()
    chunked_liked_artist_ids = chunk(liked_artist_ids, 50)
    chunked_liked_artist_features = [get_artist_features(
        spotify, chunked_artists)['artists'] for chunked_artists in tqdm(chunked_liked_artist_ids)]
    liked_artist_features = [val for val in list(
        chain.from_iterable(chunked_liked_artist_features)) if val]
    flattened_liked_artist_features = [flatten_artist_features(
        artist) for artist in liked_artist_features]
    liked_artist_features_df = pd.DataFrame(flattened_liked_artist_features)

    liked_songs_info_df = pd.merge(liked_tracks_df, liked_track_features_df, on="track_spid").merge(
        liked_artist_features_df, on="artist_spid").sort_values("added_at", ascending=False)
    liked_songs_info_df['interaction_style'] = "Liked Songs"

    data_dir = Path(Path().resolve(), "data")
    print(data_dir)
    spotify_path = Path(data_dir, f"{spotify.me()['id']}.csv")
    liked_songs_info_df.to_csv(spotify_path, index=False)

    return liked_songs_info_df


if __name__ == "__main__":
    main()

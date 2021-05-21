import os

import numpy as np
import pandas as pd
from pymongo import MongoClient, ReplaceOne

from .utils import chunk

MONGO_CONN = os.getenv("MONGO_CONN")

mongo = MongoClient(MONGO_CONN)
mongo_spotify_data = mongo["SpotifyData"]
mongo_spotify_tracks = mongo_spotify_data["Tracks"]
mongo_spotify_artists = mongo_spotify_data["Artists"]


def set_mongo_track_data(df_name, info_df):
    ops_list = []
    if df_name == "liked_track_features":
        db_coll = mongo_spotify_tracks
        id_col = "track_spid"
    elif df_name == "liked_track_artist_features":
        db_coll = mongo_spotify_artists
        id_col = "artist_spid"
        info_df["artist_genres"] = info_df["artist_genres"].map(list)
    else:
        return False
    feature_records = info_df.to_dict("records")

    for record in feature_records:
        ops_list.append(ReplaceOne({id_col: record[id_col]}, record, upsert=True))
    chunked_ops = chunk(ops_list, 1000)
    for ops in chunked_ops:
        db_coll.bulk_write(ops, ordered=False)
    return True


# TODO: Return Tuple to dict?
# TODO: Unpack kwargs?
def get_mongo_track_data(df_name, kwargs):
    if df_name == "track_features":
        found_tracks_data = mongo_spotify_tracks.find(
            {"track_spid": {"$in": kwargs["track_ids"]}}
        )
        found_tracks_df = pd.DataFrame(list(found_tracks_data))
        del found_tracks_df["_id"]
        found_track_ids = found_tracks_df["track_spid"].unique().tolist()
        missing_track_ids = np.setdiff1d(kwargs["track_ids"], found_track_ids)
        data = (found_tracks_df, missing_track_ids)

    elif df_name == "artist_features":
        found_artists_data = mongo_spotify_artists.find(
            {"artist_spid": {"$in": kwargs["artist_ids"]}}
        )
        found_artist_df = pd.DataFrame(list(found_artists_data))
        del found_artist_df["_id"]
        found_artist_ids = found_artist_df["artist_spid"].unique().tolist()
        missing_artist_ids = np.setdiff1d(kwargs["artist_ids"], found_artist_ids)
        data = (found_artist_df, missing_artist_ids)
    else:
        return None
    return data

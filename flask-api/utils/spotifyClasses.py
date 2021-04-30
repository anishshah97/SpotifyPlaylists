import datetime
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import redis
from dotenv import find_dotenv, load_dotenv
from pymongo import MongoClient, ReplaceOne

from .localData import gather_local_cached_data
from .spotifyData import (
    get_artist_features_df,
    get_liked_tracks_df,
    get_track_features_df,
)
from .utils import chunk

load_dotenv(find_dotenv())

# DATE_FORMAT_STRING = "%m-%d-%Y-%H-%M-%S"
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
MONGO_CONN = os.getenv("MONGO_CONN")

# BUG: Move to session class? Or is one global connection okay?
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
mongo = MongoClient(MONGO_CONN)
mongo_spotify_data = mongo["SpotifyData"]
mongo_spotify_tracks = mongo_spotify_data["Tracks"]
mongo_spotify_artists = mongo_spotify_data["Artists"]

# TODO: MAke functional?


class spotifyUserSession:
    # INIT
    def __init__(self, spotify, origin_data_source=None, export_data_source=None):
        self._spotify = spotify
        self._origin_data_source = origin_data_source
        self._export_data_source = export_data_source
        self._session_time = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()  # .strftime(DATE_FORMAT_STRING)
        # BUG: Running this will always result on a profile API request. Involving caching in this too?
        self._spotify_user_profile = self._spotify.me()
        self._default_df_names = [
            "liked_tracks",
            "liked_track_features",
            "liked_track_artist_features",
        ]
        # TODO: Abstract this away?
        self._info_dfs = {df_name: None for df_name in self._default_df_names}

    # SETTERS
    def set_export_data_source(self, export_data_source=None):
        if export_data_source:
            self._export_data_source = export_data_source
        return None

    def set_origin_data_source(self, origin_data_source=None):
        if origin_data_source:
            self._origin_data_source = origin_data_source
        return None

    # NOTE: _info_dfs should be a dict containing data
    def set_session_data(self, info_dfs=None, update=True):

        if isinstance(info_dfs, dict):
            if update:
                self._info_dfs.update(info_dfs)
            else:
                self._info_dfs = info_dfs
        # else:
        # BUG: change fallback default behavior?
        # self._info_dfs = self.bulk_get_session_data()

        return None

    def bulk_get_session_data(self, df_names="default"):

        if df_names == "default":
            dfs_to_import = {
                df_name: self._origin_data_source for df_name in self._default_df_names
            }
        elif isinstance(df_names, list):
            if len(df_names) > 0:
                # TODO: add a check to see if in provided data store before assuming it is. Allowing to break on purpose
                dfs_to_import = {
                    df_name: self._origin_data_source
                    for df_name in self._default_df_names
                }
        elif isinstance(df_names, dict):
            dfs_to_import = df_names
        else:
            raise ValueError("Improper data type for df_names")

        info_dfs = {}
        for df_name, origin_data_source in dfs_to_import.items():
            if df_name == "liked_tracks":
                info_dfs[df_name] = self.get_session_data(
                    df_name, origin_data_source, {}
                )
            elif df_name == "liked_track_features":
                # TODO: Abstract away as opposed to hard coding liked_tracks
                track_ids = info_dfs["liked_tracks"]["track_spid"].unique().tolist()
                info_dfs[df_name] = self.get_session_data(
                    df_name, origin_data_source, {"track_ids": track_ids}
                )
            elif df_name == "liked_track_artist_features":
                artist_ids = info_dfs["liked_tracks"]["artist_spid"].unique().tolist()
                info_dfs[df_name] = self.get_session_data(
                    df_name, origin_data_source, {"artist_ids": artist_ids}
                )

        return info_dfs

    def get_and_update_user_liked_tracks_data(self):
        current_liked_tracks_df = self.get_session_data("liked_tracks", "spotify", {})
        print(f"current_liked_tracks_df.shape:{current_liked_tracks_df.shape}")
        self.store_session_data("liked_tracks", current_liked_tracks_df, "redis")
        # self.store_session_data("liked_tracks", current_liked_tracks_df, "s3")

        cached_liked_track_features_df, missing_track_ids = self.get_session_data(
            "track_features",
            "mongo",
            {"track_ids": current_liked_tracks_df["track_spid"].unique().tolist()},
        )
        print(
            f"cached_liked_track_features_df.shape:{cached_liked_track_features_df.shape}"
        )
        print(f"len(missing_track_ids):{len(missing_track_ids)}")

        cached_artist_track_features_df, missing_artist_ids = self.get_session_data(
            "artist_features",
            "mongo",
            {"artist_ids": current_liked_tracks_df["artist_spid"].unique().tolist()},
        )
        print(
            f"cached_artist_track_features_df.shape:{cached_artist_track_features_df.shape}"
        )
        print(f"len(missing_artist_ids):{len(missing_artist_ids)}")

        if len(missing_track_ids) > 0:
            remaining_track_features_df = self.get_session_data(
                "liked_track_features", "spotify", {"track_ids": missing_track_ids}
            )
            self.store_session_data(
                "track_features", remaining_track_features_df, "mongo"
            )
            print(
                f"remaining_track_features_df.shape:{remaining_track_features_df.shape}"
            )
        if len(missing_artist_ids) > 0:
            remaining_artist_features_df = self.get_session_data(
                "liked_track_artist_features",
                "spotify",
                {"artist_ids": missing_artist_ids},
            )
            self.store_session_data(
                "artist_features", remaining_artist_features_df, "mongo"
            )
            print(
                f"remaining_artist_features_df.shape:{remaining_artist_features_df.shape}"
            )
        track_features_df = pd.concat(
            [cached_liked_track_features_df, remaining_track_features_df]
        )
        print(f"track_features_df.shape:{track_features_df.shape}")
        artist_features_df = pd.concat(
            [cached_artist_track_features_df, remaining_artist_features_df]
        )
        print(f"artist_features_df.shape:{artist_features_df.shape}")

        user_liked_session_data = {
            "liked_tracks": current_liked_tracks_df,
            "liked_track_features": track_features_df,
            "liked_track_artist_features": artist_features_df,
        }

        return user_liked_session_data
        # concat, process, and return dfs

    def get_user_liked_tracks_data(self):
        # BUG: Forcing to be a pandas dataframe as a return response
        cached_liked_tracks_df = self.get_session_data("liked_tracks", "redis", {})
        if not isinstance(cached_liked_tracks_df, pd.DataFrame):
            cached_liked_tracks_df = self.get_session_data("liked_tracks", "s3", {})
            if not isinstance(cached_liked_tracks_df, pd.DataFrame):
                return self.get_and_update_user_liked_tracks_data()
            else:
                raise ValueError(
                    "Something went wrong when pulling get user liked tracks"
                )
        print(f"cached_liked_tracks_df.shape:{cached_liked_tracks_df.shape}")

        cached_liked_track_features_df, _ = self.get_session_data(
            "track_features",
            "mongo",
            {"track_ids": cached_liked_tracks_df["track_spid"].unique().tolist()},
        )
        print(
            f"cached_liked_track_features_df.shape:{cached_liked_track_features_df.shape}"
        )
        cached_artist_track_features_df, _ = self.get_session_data(
            "artist_features",
            "mongo",
            {"artist_ids": cached_liked_tracks_df["artist_spid"].unique().tolist()},
        )
        print(
            f"cached_artist_track_features_df.shape:{cached_artist_track_features_df.shape}"
        )
        user_liked_session_data = {
            "liked_tracks": cached_liked_tracks_df,
            "liked_track_features": cached_liked_track_features_df,
            "liked_track_artist_features": cached_artist_track_features_df,
        }
        return user_liked_session_data
        # concat, process, and return dfs

    def get_session_data(self, df_name, origin_data_source, kwargs={}):
        user_id = self._spotify_user_profile["id"]
        if not isinstance(df_name, str):
            raise ValueError("Must pass string for df_name")
        if not isinstance(kwargs, dict):
            raise ValueError("Must pass dict for kwargs")

        if origin_data_source == "local":
            print("using local cached data")
            kwargs["df_name"] = df_name
            kwargs["user_id"] = user_id
            session_data = gather_local_cached_data(**kwargs)
        elif origin_data_source == "s3":
            print("using s3 cached data")
            pass
        elif origin_data_source == "redis":
            print("using redis cached data")
            data_path = f"user:{user_id}:{df_name}"
            # BUG: assuming object pickled and cached in redis as such will return none default non pickle
            pickled_data = r.get(data_path)
            if pickled_data:
                session_data = pickle.loads(pickled_data)
            else:
                session_data = pickled_data
        elif origin_data_source == "mongo":
            print("using mongo pulled data")
            if df_name == "track_features":
                found_tracks_data = mongo_spotify_tracks.find(
                    {"track_spid": {"$in": kwargs["track_ids"]}}
                )
                found_tracks_df = pd.DataFrame(list(found_tracks_data))
                del found_tracks_df["_id"]
                found_track_ids = found_tracks_df["track_spid"].unique().tolist()
                missing_track_ids = np.setdiff1d(kwargs["track_ids"], found_track_ids)
                session_data = (found_tracks_df, missing_track_ids)

            elif df_name == "artist_features":
                found_artists_data = mongo_spotify_artists.find(
                    {"artist_spid": {"$in": kwargs["artist_ids"]}}
                )
                found_artist_df = pd.DataFrame(list(found_artists_data))
                del found_artist_df["_id"]
                found_artist_ids = found_artist_df["artist_spid"].unique().tolist()
                missing_artist_ids = np.setdiff1d(
                    kwargs["artist_ids"], found_artist_ids
                )
                session_data = (found_artist_df, missing_artist_ids)
        else:
            print("pulling data from spotify")
            spotify = self._spotify
            kwargs["spotify"] = spotify
            if df_name == "liked_tracks":
                session_data = get_liked_tracks_df(**kwargs)
            elif df_name == "liked_track_features":
                session_data = get_track_features_df(**kwargs)
            elif df_name == "liked_track_artist_features":
                session_data = get_artist_features_df(**kwargs)
            else:
                raise ValueError(f"Not a valid df_name: {df_name}")
        return session_data

    # - Default stores to wherever in self.store
    def bulk_store_session_data(self, df_names="all"):

        if df_names == "all":
            dfs_to_export = {
                df_name: self._export_data_source for df_name in self._info_dfs.keys()
            }
        elif isinstance(df_names, list):
            if len(df_names) > 0:
                dfs_to_export = {}
                for df_name in df_names:
                    if df_name in self._info_dfs:
                        dfs_to_export[df_name] = self._export_data_source
                    else:
                        print(f"{df_name} doesn't exist in this data")
        elif isinstance(df_names, dict):
            if len(df_names) > 0:
                dfs_to_export = {}
                for df_name, export_data_source in df_names.items():
                    if df_name in self._info_dfs:
                        dfs_to_export[df_name] = self._export_data_source
                    else:
                        print(f"{df_name} doesn't exist in this data")
        else:
            raise ValueError("Improper data type for df_names")

        for df_name, export_data_source in dfs_to_export.items():
            print("------------")
            print(df_name)
            info_df = self._info_dfs[df_name]
            if isinstance(info_df, pd.DataFrame):
                if self.store_session_data(df_name, info_df, export_data_source):
                    print("successful save")
                    print("OOOOOOOOOOOOO")
                else:
                    print("didnt save")
                    print("XXXXXXXXXXXXX")
            else:
                print(f"{df_name} contains no data!")

        return None

    # TODO: Rename function and variable names
    def store_session_data(self, df_name, info_df, export_data_source):
        if export_data_source:
            data_path = self.decide_export_path(df_name, export_data_source)
            print(f"storing to {data_path}")
            if export_data_source == "local":
                print("local _export_data_source")
                info_df.to_parquet(data_path, index=False)
                return True
            elif export_data_source == "s3":
                print("s3 _export_data_source")
                info_df.to_parquet(
                    data_path,
                    index=False,
                    storage_options={
                        "key": AWS_ACCESS_KEY_ID,
                        "secret": AWS_SECRET_ACCESS_KEY,
                    },
                )
                return True
            elif export_data_source == "redis":
                print("redis _export_data_source")
                # NOTE: expire after 1 day (86400 seconds)
                r.set(
                    data_path,
                    pickle.dumps(info_df),
                    ex=86400,
                )
                return True
            elif export_data_source == "mongo":
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
                    ops_list.append(
                        ReplaceOne({id_col: record[id_col]}, record, upsert=True)
                    )
                chunked_ops = chunk(ops_list, 1000)
                for ops in chunked_ops:
                    db_coll.bulk_write(ops, ordered=False)
                return True
            else:
                return False
        else:
            return False

        return False

    # TODO: Rename function name
    def decide_export_path(self, df_name, export_data_source):
        user_id = self._spotify_user_profile["id"]
        date_time = self._session_time

        data_path = False
        file_name = f"{df_name}.parquet"
        if export_data_source == "local":
            print("local path")
            raw_data_dir = Path(Path().resolve().parent, "data", "raw")
            user_path = Path(raw_data_dir, "users", user_id)
            session_time_path = Path(user_path, str(date_time))
            session_time_path.mkdir(parents=True, exist_ok=True)
            data_path = Path(session_time_path, file_name)
        elif export_data_source == "s3":
            print("s3 path")
            file_path = f"{user_id}/{date_time}/{file_name}"
            data_path = f"s3://{AWS_S3_BUCKET}/raw/users/{file_path}"
        elif export_data_source == "redis":
            print("redis path")
            data_path = f"user:{user_id}:{df_name}"
        elif export_data_source == "mongo":
            print("mongo path not needed")
        return data_path

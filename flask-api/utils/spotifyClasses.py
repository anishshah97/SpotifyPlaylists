import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import os
import redis
from pymongo import MongoClient, ReplaceOne
import pickle
from .spotifyData import gather_liked_tracks_data
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
# TODO: Change name to spotifyRunner or something as calling this user seems improper
# TODO: Fix variable names
# - cached_data -> origin_data_path
# - store -> export_data_path
class spotifyUser:
    def __init__(self, spotify, cached_data=None, store=None):
        self.spotify = spotify
        self.cached_data = cached_data
        self.store = store
        self.session_time = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()  # .strftime(DATE_FORMAT_STRING)
        # BUG: Running this will always result on a profile API request. Involving caching in this too?
        self.spotify_me = self.spotify.me()
        self.default_liked_df_names = [
            "liked_tracks",
            "liked_track_features",
            "liked_track_artist_features",
        ]
        # TODO: Abstract this away?
        self.liked_songs_info = {df_name: None for df_name in self.default_liked_df_names}

    def set_store(self, store=None):
        if store:
            self.store = store
        return None

    def set_cached_data(self, cached_data=None):
        if cached_data:
            self.cached_data = cached_data
        return None

    # NOTE: list of names of files to pull from for a spotifyuser session
    # NOTE: we will always want to pull the latest data from the cache for now
    # TODO: Change name of function
    # TODO: change name of variable
    def pull_liked_songs_data(self, df_names=None, cached_data=None):
        if not cached_data:
            cached_data = self.cached_data
        if not df_names:
            df_names = self.default_liked_df_names
        spotify = self.spotify
        user_id = self.spotify_me["id"]
        if cached_data == "local":
            print("using local cached data")
            raw_data_dir = Path(Path().resolve().parent, "data", "raw")
            user_path = Path(raw_data_dir, "users", user_id)
            date_folder_paths = {
                date_path: datetime.datetime.fromisoformat(date_path.name)
                for date_path in user_path.glob("*/")
            }
            liked_songs_info_dfs = {}
            for df_name in df_names:
                spotify_data_path = self.decide_local_cache_path(
                    user_path, date_folder_paths, df_name
                )
                print(f"opening {spotify_data_path}")
                # TODO: If file doesnt exist then an error will throw
                liked_songs_info_dfs[df_name] = pd.read_parquet(spotify_data_path)
        elif cached_data == "s3":
            print("using s3 cached data")
            pass
        elif cached_data == "redis":
            print("using redis cached data")
            pass
        elif cached_data == "mongo":
            print("using mongo pulled data")
        else:
            print("pulling data from spotify")
            liked_songs_info_dfs = gather_liked_tracks_data(spotify)
        return liked_songs_info_dfs

    def decide_local_cache_path(self, user_path, date_folder_paths, df_name):
        df_file_name = df_name + ".parquet"
        df_date_folders = dict(
            filter(lambda elem: Path(elem[0], df_file_name).is_file(), date_folder_paths.items())
        )
        latest_session_date = max(df_date_folders, key=df_date_folders.get)
        session_path = Path(user_path, latest_session_date)
        spotify_data_path = Path(session_path, df_file_name)
        return spotify_data_path

    # TODO: Rename function name
    def decide_storage_path(self, df_name):
        store = self.store
        user_id = self.spotify_me["id"]
        date_time = self.session_time

        spotify_data_path = False
        file_name = f"{df_name}.parquet"
        if store == "local":
            print("local path")
            raw_data_dir = Path(Path().resolve().parent, "data", "raw")
            user_path = Path(raw_data_dir, "users", user_id)
            session_time_path = Path(user_path, str(date_time))
            session_time_path.mkdir(parents=True, exist_ok=True)
            spotify_data_path = Path(session_time_path, file_name)
        elif store == "s3":
            print("s3 path")
            file_path = f"{user_id}/{date_time}/{file_name}"
            spotify_data_path = f"s3://{AWS_S3_BUCKET}/raw/users/{file_path}"
        elif store == "redis":
            print("redis path")
            pass
        elif store == "mongo":
            print("mongo path not needed")
        return spotify_data_path

    # TODO: Rename function and variable names
    def decide_storage_and_path(self, df_name, liked_songs_info_df):
        store = self.store
        if store:
            spotify_data_path = self.decide_storage_path(df_name)
            print(f"storing to {spotify_data_path}")
            if store == "local":
                print("local store")
                liked_songs_info_df.to_parquet(spotify_data_path, index=False)
                return True
            elif store == "s3":
                print("s3 store")
                liked_songs_info_df.to_parquet(
                    spotify_data_path,
                    index=False,
                    storage_options={"key": AWS_ACCESS_KEY_ID, "secret": AWS_SECRET_ACCESS_KEY},
                )
                return True
            elif store == "redis":
                print("redis store")
                if df_name in ["liked_tracks"]:
                    user_id = self.spotify_me["id"]
                    if df_name == "liked_tracks":
                        # NOTE: expire after 1 day
                        r.set(
                            "user:" + user_id + ":liked_tracks",
                            pickle.dumps(liked_songs_info_df),
                            ex=86400,
                        )
                        return True
                    else:
                        return False
                    # context.deserialize(r.get("key"))
            elif store == "mongo":
                ops_list = []
                if df_name in ["liked_track_features", "liked_track_artist_features"]:

                    if df_name == "liked_track_features":
                        db_coll = mongo_spotify_tracks
                        id_col = "track_spid"
                    elif df_name == "liked_track_artist_features":
                        db_coll = mongo_spotify_artists
                        id_col = "artist_spid"
                        liked_songs_info_df["artist_genres"] = liked_songs_info_df[
                            "artist_genres"
                        ].map(list)
                    feature_records = liked_songs_info_df.to_dict("records")

                    for record in feature_records:
                        ops_list.append(ReplaceOne({id_col: record[id_col]}, record, upsert=True))
                    chunked_ops = chunk(ops_list, 1000)
                    for ops in chunked_ops:
                        db_coll.bulk_write(ops, ordered=False)
                    return True
                else:
                    return False
            else:
                return False

        return False

    # NOTE: liked_songs_info should be a dict containing data
    def set_users_liked_song_info(self, update=True, liked_songs_info=None):

        if isinstance(liked_songs_info, dict):
            if update:
                self.liked_songs_info.update(liked_songs_info)
            else:
                self.liked_songs_info = liked_songs_info
        else:
            # BUG: change fallback default behavior?
            self.liked_songs_info = self.pull_liked_songs_data()

        return None

    # NOTE: file_names should be a list of df names in the keys to export
    # TODO: pass json of filename:storage_option to do export
    # - Default stores to wherever in self.store
    def export_liked_songs(self, file_names="all"):

        dfs_to_export = []
        if file_names == "all":
            dfs_to_export = self.liked_songs_info.keys()
        elif isinstance(file_names, list):
            if len(file_names) > 0:
                for file_name in file_names:
                    if file_name in self.liked_songs_info:
                        dfs_to_export.append(file_name)
                    else:
                        print(f"{file_name} doesn't exist in this data")

        for df_name in dfs_to_export:
            print("------------")
            print(df_name)
            liked_songs_info_df = self.liked_songs_info[df_name]
            if isinstance(liked_songs_info_df, pd.DataFrame):
                if self.decide_storage_and_path(df_name, liked_songs_info_df):
                    print("successful save")
                    print("OOOOOOOOOOOOO")
                else:
                    print("didnt save")
                    print("XXXXXXXXXXXXX")
            else:
                print(f"{df_name} contains no data!")

        return None

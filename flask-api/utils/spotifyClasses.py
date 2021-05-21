import datetime
import os
from pathlib import Path

import pandas as pd

# TODO: Better control over loading .env files
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from .awsData import set_aws_data
from .localData import get_local_cached_data, set_local_cached_data
from .mongoData import get_mongo_track_data, set_mongo_track_data
from .redisData import get_redis_data, set_redis_data
from .spotifyData import (
    get_artist_features_df,
    get_liked_tracks_df,
    get_track_features_df,
)
from .utils import logger

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")


class spotifyUserSession:
    # INIT
    def __init__(
        self, spotify, origin_data_source=None, export_data_source=None, **kwargs
    ):
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

    # GETTERS
    # Get session data from the provided sources
    # NOTE - Can pass in dict containing each thing you want to get and the origin of where it came from
    def bulk_get_session_data(self, df_names="default"):
        origin_data_source = self._origin_data_source
        default_df_names = self._default_df_names

        if df_names == "default":
            dfs_to_import = {
                df_name: origin_data_source for df_name in default_df_names
            }
        elif isinstance(df_names, list):
            if len(df_names) > 0:
                # TODO: add a check to see if in provided data store before assuming it is. Allowing to break on purpose
                dfs_to_import = {df_name: origin_data_source for df_name in df_names}
        elif isinstance(df_names, dict):
            dfs_to_import = df_names
        else:
            raise ValueError("Improper data type for df_names")

        info_dfs = {}
        # BUG: If liked tracks isnt first then this will break, use dict get for each sequentially to force order?
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
            else:
                logger.debug(f"{df_name} does not exist in {origin_data_source}")

        return info_dfs

    # TODO: Implement proper kwargs?
    def get_session_data(self, df_name, origin_data_source, kwargs={}):
        user_id = self._spotify_user_profile["id"]
        if not isinstance(df_name, str):
            raise ValueError("Must pass string for df_name")
        if not isinstance(kwargs, dict):
            raise ValueError("Must pass dict for kwargs")

        if origin_data_source == "local":
            logger.debug("using local cached data")
            kwargs["df_name"] = df_name
            kwargs["user_id"] = user_id
            session_data = get_local_cached_data(**kwargs)
        elif origin_data_source == "s3":
            logger.debug("using s3 cached data")
            # TODO: implement getting from aws
            raise ValueError("Not yet implemented!")
        elif origin_data_source == "redis":
            logger.debug("using redis cached data")
            data_path = f"user:{user_id}:{df_name}"
            # BUG: assuming object pickled and cached in redis as such will return none default non pickle
            session_data = get_redis_data(data_path)
        elif origin_data_source == "mongo":
            logger.debug("using mongo pulled data")
            session_data = get_mongo_track_data(df_name, kwargs)
        else:
            logger.debug("pulling data from spotify")
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

    # STORERS
    # Saves the data points to the provided destination
    # NOTE - Default stores to wherever in self.store
    def bulk_store_session_data(self, df_names="all"):
        export_data_source = self._export_data_source
        info_dfs = self._info_dfs

        if df_names == "all":
            dfs_to_export = {df_name: export_data_source for df_name in info_dfs.keys()}
        elif isinstance(df_names, list):
            if len(df_names) > 0:
                dfs_to_export = {}
                for df_name in df_names:
                    if df_name in info_dfs:
                        dfs_to_export[df_name] = export_data_source
                    else:
                        logger.debug(f"{df_name} doesn't exist in this data")
        elif isinstance(df_names, dict):
            if len(df_names) > 0:
                dfs_to_export = {}
                for df_name, export_data_source in df_names.items():
                    if df_name in info_dfs:
                        dfs_to_export[df_name] = export_data_source
                    else:
                        logger.debug(f"{df_name} doesn't exist in this data")
        else:
            raise ValueError("Improper data type for df_names")

        for df_name, export_data_source in dfs_to_export.items():
            logger.debug("------------")
            logger.debug(df_name)
            info_df = info_dfs[df_name]
            if isinstance(info_df, pd.DataFrame):
                if self.store_session_data(df_name, info_df, export_data_source):
                    logger.debug("successful save")
                    logger.debug("OOOOOOOOOOOOO")
                else:
                    logger.debug("didnt save")
                    logger.debug("XXXXXXXXXXXXX")
            else:
                logger.debug(f"{df_name} contains no data!")

        return None

    # TODO: Rename function and variable names
    # TODO: Implement proper kwargs?
    def store_session_data(self, df_name, info_df, export_data_source):
        if export_data_source:
            data_path = self.decide_export_path(df_name, export_data_source)
            logger.debug(f"storing to {data_path}")
            if export_data_source == "local":
                logger.debug("local _export_data_source")
                return set_local_cached_data(data_path, info_df)
            elif export_data_source == "s3":
                logger.debug("s3 _export_data_source")
                return set_aws_data(data_path, info_df)
            elif export_data_source == "redis":
                logger.debug("redis _export_data_source")
                return set_redis_data(data_path, info_df)
            elif export_data_source == "mongo":
                return set_mongo_track_data(df_name, info_df)
            else:
                return False
        else:
            return False

    # TODO: Rename function name
    # TODO: Allow for saving of other files formats other than parquet
    # TODO: Move to the specific storer desitination file?
    def decide_export_path(self, df_name, export_data_source):
        user_id = self._spotify_user_profile["id"]
        date_time = self._session_time

        data_path = False
        file_name = f"{df_name}.parquet"
        if export_data_source == "local":
            logger.debug("local path")
            raw_data_dir = Path(Path().resolve().parent, "data", "raw")
            user_path = Path(raw_data_dir, "users", user_id)
            session_time_path = Path(user_path, str(date_time))
            session_time_path.mkdir(parents=True, exist_ok=True)
            data_path = Path(session_time_path, file_name)
        elif export_data_source == "s3":
            logger.debug("s3 path")
            file_path = f"{user_id}/{date_time}/{file_name}"
            data_path = f"s3://{AWS_S3_BUCKET}/raw/users/{file_path}"
        elif export_data_source == "redis":
            logger.debug("redis path")
            data_path = f"user:{user_id}:{df_name}"
        elif export_data_source == "mongo":
            logger.debug("mongo path not needed")
        return data_path

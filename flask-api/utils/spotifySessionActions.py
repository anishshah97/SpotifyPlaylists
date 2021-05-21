import pandas as pd

from .utils import logger


def get_and_update_user_liked_tracks_data(spot_user_session):
    current_liked_tracks_df = spot_user_session.get_session_data(
        "liked_tracks", "spotify", {}
    )
    logger.debug(f"current_liked_tracks_df.shape:{current_liked_tracks_df.shape}")
    spot_user_session.store_session_data(
        "liked_tracks", current_liked_tracks_df, "redis"
    )
    # spot_user_session.store_session_data("liked_tracks", current_liked_tracks_df, "s3")

    (
        cached_liked_track_features_df,
        missing_track_ids,
    ) = spot_user_session.get_session_data(
        "track_features",
        "mongo",
        {"track_ids": current_liked_tracks_df["track_spid"].unique().tolist()},
    )
    logger.debug(
        f"cached_liked_track_features_df.shape:{cached_liked_track_features_df.shape}"
    )
    logger.debug(f"len(missing_track_ids):{len(missing_track_ids)}")

    (
        cached_artist_track_features_df,
        missing_artist_ids,
    ) = spot_user_session.get_session_data(
        "artist_features",
        "mongo",
        {"artist_ids": current_liked_tracks_df["artist_spid"].unique().tolist()},
    )
    logger.debug(
        f"cached_artist_track_features_df.shape:{cached_artist_track_features_df.shape}"
    )
    logger.debug(f"len(missing_artist_ids):{len(missing_artist_ids)}")

    if len(missing_track_ids) > 0:
        remaining_track_features_df = spot_user_session.get_session_data(
            "liked_track_features", "spotify", {"track_ids": missing_track_ids}
        )
        spot_user_session.store_session_data(
            "track_features", remaining_track_features_df, "mongo"
        )
        logger.debug(
            f"remaining_track_features_df.shape:{remaining_track_features_df.shape}"
        )
    if len(missing_artist_ids) > 0:
        remaining_artist_features_df = spot_user_session.get_session_data(
            "liked_track_artist_features",
            "spotify",
            {"artist_ids": missing_artist_ids},
        )
        spot_user_session.store_session_data(
            "artist_features", remaining_artist_features_df, "mongo"
        )
        logger.debug(
            f"remaining_artist_features_df.shape:{remaining_artist_features_df.shape}"
        )
    track_features_df = pd.concat(
        [cached_liked_track_features_df, remaining_track_features_df]
    )
    logger.debug(f"track_features_df.shape:{track_features_df.shape}")
    artist_features_df = pd.concat(
        [cached_artist_track_features_df, remaining_artist_features_df]
    )
    logger.debug(f"artist_features_df.shape:{artist_features_df.shape}")

    user_liked_session_data = {
        "liked_tracks": current_liked_tracks_df,
        "liked_track_features": track_features_df,
        "liked_track_artist_features": artist_features_df,
    }

    return user_liked_session_data
    # concat, process, and return dfs


def get_user_liked_tracks_data(spot_user_session):
    # BUG: Forcing to be a pandas dataframe as a return response
    cached_liked_tracks_df = spot_user_session.get_session_data(
        "liked_tracks", "redis", {}
    )
    if not isinstance(cached_liked_tracks_df, pd.DataFrame):
        cached_liked_tracks_df = spot_user_session.get_session_data(
            "liked_tracks", "s3", {}
        )
        if not isinstance(cached_liked_tracks_df, pd.DataFrame):
            return spot_user_session.get_and_update_user_liked_tracks_data()
        else:
            raise ValueError("Something went wrong when pulling get user liked tracks")
    logger.debug(f"cached_liked_tracks_df.shape:{cached_liked_tracks_df.shape}")

    cached_liked_track_features_df, _ = spot_user_session.get_session_data(
        "track_features",
        "mongo",
        {"track_ids": cached_liked_tracks_df["track_spid"].unique().tolist()},
    )
    logger.debug(
        f"cached_liked_track_features_df.shape:{cached_liked_track_features_df.shape}"
    )
    cached_artist_track_features_df, _ = spot_user_session.get_session_data(
        "artist_features",
        "mongo",
        {"artist_ids": cached_liked_tracks_df["artist_spid"].unique().tolist()},
    )
    logger.debug(
        f"cached_artist_track_features_df.shape:{cached_artist_track_features_df.shape}"
    )
    user_liked_session_data = {
        "liked_tracks": cached_liked_tracks_df,
        "liked_track_features": cached_liked_track_features_df,
        "liked_track_artist_features": cached_artist_track_features_df,
    }
    return user_liked_session_data
    # concat, process, and return dfs

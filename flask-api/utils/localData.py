import datetime
from pathlib import Path

import pandas as pd


# TODO: allow other file paths other than parquet
def decide_latest_local_cache_path(user_path, date_folder_paths, df_name):
    df_file_name = df_name + ".parquet"
    df_date_folders = dict(
        filter(
            lambda elem: Path(elem[0], df_file_name).is_file(),
            date_folder_paths.items(),
        )
    )
    latest_session_date = max(df_date_folders, key=df_date_folders.get)
    session_path = Path(user_path, latest_session_date)
    data_path = Path(session_path, df_file_name)
    return data_path


def get_local_cached_data(user_id, df_name, **kwargs):
    raw_data_dir = Path(Path().resolve().parent, "data", "raw")
    user_path = Path(raw_data_dir, "users", user_id)
    date_folder_paths = {
        date_path: datetime.datetime.fromisoformat(date_path.name)
        for date_path in user_path.glob("*/")
    }
    data_path = decide_latest_local_cache_path(user_path, date_folder_paths, df_name)
    print(f"opening {data_path}")
    # BUG: If file doesnt exist then an error will throw
    return pd.read_parquet(data_path)


# TODO: Generalize to different file types
def set_local_cached_data(data_path, info_df):
    info_df.to_parquet(data_path, index=False)
    return True

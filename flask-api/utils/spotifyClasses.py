from datetime import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import os
from .spotifyData import gather_liked_tracks_data

load_dotenv(find_dotenv())

date_format_string = "%m-%d-%Y-%H-%M-%S"


class spotifyUser:
    def __init__(self, spotify, testing=False, store=False, local=False):
        self.spotify = spotify
        self.testing = testing
        self.store = store
        self.local = local
        self.session_time = datetime.now().strftime(date_format_string)
        self.spotify_me = self.spotify.me()
        self.liked_songs_info = {
            "liked_tracks": None,
            "liked_track_features": None,
            "liked_track_artist_features": None,
        }

    def pull_liked_songs_data(self):
        testing = self.testing
        spotify = self.spotify
        user_id = self.spotify_me["id"]
        liked_song_file_names = self.liked_songs_info.keys()
        if testing:
            print("testing")
            data_dir = Path(Path().resolve().parent.parent, "data")
            user_path = Path(data_dir, user_id)
            date_folder_paths = {
                date_path: datetime.strptime(date_path.name, date_format_string)
                for date_path in user_path.glob("*/")
            }
            latest_session_date = max(date_folder_paths, key=date_folder_paths.get)
            session_path = Path(user_path, latest_session_date)
            liked_songs_info_dfs = {}
            for df_name in liked_song_file_names:
                spotify_data_path = Path(session_path, df_name + ".csv")
                print(f"opening {spotify_data_path}")
                liked_songs_info_dfs[df_name] = pd.read_csv(spotify_data_path)

        else:
            print("pulling spotify")
            liked_songs_info_dfs = gather_liked_tracks_data(spotify)
        return liked_songs_info_dfs

    def decide_path(self, df_name):
        AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
        local = self.local
        user_id = self.spotify_me["id"]
        date_time = self.session_time

        file_name = f"{df_name}.csv"
        if local:
            print("local path")
            data_dir = Path(Path().resolve().parent.parent, "data")
            user_path = Path(data_dir, user_id)
            session_time_path = Path(user_path, date_time)
            session_time_path.mkdir(parents=True, exist_ok=True)
            spotify_data_path = Path(session_time_path, file_name)
        else:
            print("s3 path")
            file_path = f"{user_id}/{date_time}/{file_name}"
            spotify_data_path = f"s3://{AWS_S3_BUCKET}/{file_path}"
        return spotify_data_path

    def decide_storage_and_path(self, liked_songs_info_dict):
        store = self.store
        local = self.local
        if store:
            df_name = liked_songs_info_dict[0]
            liked_songs_info_df = liked_songs_info_dict[1]
            spotify_data_path = self.decide_path(df_name)
            print(f"storing to {spotify_data_path}")
            if local:
                print("local store")
                liked_songs_info_df.to_csv(spotify_data_path, index=False)
            else:
                print("s3 store")
                AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
                AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
                liked_songs_info_df.to_csv(
                    spotify_data_path,
                    index=False,
                    storage_options={"key": AWS_ACCESS_KEY_ID, "secret": AWS_SECRET_ACCESS_KEY},
                )

        return None

    def set_users_liked_song_info(self):

        self.liked_songs_info = self.pull_liked_songs_data()

        return None

    def export_liked_songs(self):

        for liked_songs_info_dict in self.liked_songs_info.items():
            self.decide_storage_and_path(liked_songs_info_dict)

        return None

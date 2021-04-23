from datetime import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import os
from .spotifyData import gather_liked_tracks_data

load_dotenv(find_dotenv())

date_format_string = "%m-%d-%Y-%H-%M-%S"
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


class spotifyUser:
    def __init__(self, spotify, test_data=None, store=None):
        self.spotify = spotify
        self.test_data = test_data
        self.store = store
        self.session_time = datetime.now().strftime(date_format_string)
        self.spotify_me = self.spotify.me()
        self.liked_songs_info = {
            "liked_tracks": None,
            "liked_track_features": None,
            "liked_track_artist_features": None,
        }

    def pull_liked_songs_data(self):
        test_data = self.test_data
        spotify = self.spotify
        user_id = self.spotify_me["id"]

        liked_song_file_names = self.liked_songs_info.keys()
        if test_data == "local":
            print("using local test data")
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
        elif test_data == "s3":
            pass
        else:
            print("pulling data from spotify")
            liked_songs_info_dfs = gather_liked_tracks_data(spotify)
        return liked_songs_info_dfs

    def decide_path(self, df_name):
        store = self.store
        user_id = self.spotify_me["id"]
        date_time = self.session_time

        spotify_data_path = False
        file_name = f"{df_name}.csv"
        if store == "local":
            print("local path")
            data_dir = Path(Path().resolve().parent.parent, "data")
            user_path = Path(data_dir, user_id)
            session_time_path = Path(user_path, date_time)
            session_time_path.mkdir(parents=True, exist_ok=True)
            spotify_data_path = Path(session_time_path, file_name)
        elif store == "s3":
            print("s3 path")
            file_path = f"{user_id}/{date_time}/{file_name}"
            spotify_data_path = f"s3://{AWS_S3_BUCKET}/{file_path}"
        return spotify_data_path

    def decide_storage_and_path(self, liked_songs_info_dict):
        store = self.store
        if store:
            df_name = liked_songs_info_dict[0]
            liked_songs_info_df = liked_songs_info_dict[1]
            spotify_data_path = self.decide_path(df_name)
            print(f"storing to {spotify_data_path}")
            if store == "local":
                print("local store")
                liked_songs_info_df.to_csv(spotify_data_path, index=False)
                return True
            elif store == "s3":
                print("s3 store")
                liked_songs_info_df.to_csv(
                    spotify_data_path,
                    index=False,
                    storage_options={"key": AWS_ACCESS_KEY_ID, "secret": AWS_SECRET_ACCESS_KEY},
                )
                return True
            else:
                return False

        return False

    def set_users_liked_song_info(self, liked_songs_info=None):

        if liked_songs_info:
            self.liked_songs_info = liked_songs_info
        else:
            self.liked_songs_info = self.pull_liked_songs_data()

        return None

    def export_liked_songs(self):

        for liked_songs_info_dict in self.liked_songs_info.items():
            print(liked_songs_info_dict[0])
            if self.decide_storage_and_path(liked_songs_info_dict):
                print("successful save")
            else:
                print("didnt save")

        return None

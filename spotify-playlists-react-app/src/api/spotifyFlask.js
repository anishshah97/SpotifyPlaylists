import { createServer } from "miragejs";

const spotifyFlaskBaseAPI = "api";

function makeSpotifyFlaskServer({ environment = "test" } = {}) {
  let server = createServer({
    environment,

    routes() {
      this.namespace = spotifyFlaskBaseAPI;

      this.post(
        "/my_spotify_id",
        (schema, request) => {
          var data = {
            user: {
              spotifyName: "Anish Shah",
            },
          };
          return data;
        },
        { timing: 1000 }
      );

      this.post(
        "/my_spotify_data",
        (schema, request) => {
          var data = {
            data: {
              likedSongs: null,
              likedSongFeatures: null,
              likedSongArtistFeatures: null,
            },
          };
          return data;
        },
        { timing: 10000 }
      );
    },
  });

  return server;
}

export { spotifyFlaskBaseAPI, makeSpotifyFlaskServer };

import { createServer, Model } from "miragejs";

const spotifyFlaskBaseAPI = "api";

function makeSpotifyFlaskServer({ environment = "test" } = {}) {
  let server = createServer({
    environment,

    models: {
      user: Model,
    },

    seeds(server) {
      server.create("user", {
        spotifyName: "Anish Shah",
      });
    },

    routes() {
      this.namespace = spotifyFlaskBaseAPI;

      this.get("/users", (schema) => {
        return schema.users.all();
      });

      this.post("/my_spotify_id", (schema, request) => {
        var data = schema.users.find(1);
        return data;
      });
    },
  });

  return server;
}

export { spotifyFlaskBaseAPI, makeSpotifyFlaskServer };

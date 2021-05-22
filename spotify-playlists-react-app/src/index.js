import React from "react";
import ReactDOM from "react-dom";
import { Provider } from "react-redux";
import { Client as Styletron } from "styletron-engine-atomic";
import { DebugEngine, Provider as StyletronProvider } from "styletron-react";
import { makeSpotifyFlaskServer } from "./api/bundle";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
import configureStore from "./store";
import "./themes/index.css";

if (process.env.NODE_ENV !== "production") {
  require("dotenv").config();
  makeSpotifyFlaskServer({
    environment: process.env.NODE_ENV,
  });
}

const debug =
  process.env.NODE_ENV === "production" ? void 0 : new DebugEngine();

const engine = new Styletron();

ReactDOM.render(
  <Provider store={configureStore()}>
    <StyletronProvider value={engine} debug={debug} debugAfterHydration>
      <App />
    </StyletronProvider>
  </Provider>,
  document.getElementById("root")
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();

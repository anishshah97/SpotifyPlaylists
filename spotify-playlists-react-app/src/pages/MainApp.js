import { Div, ThemeProvider } from "atomize";
import ParticlesBg from "particles-bg";
import React, { Component } from "react";
import { connect } from "react-redux";
import TextTransition, { presets } from "react-text-transition";
import { spotifyFlaskBaseAPI } from "../api/bundle";
import { introContainer, particleBg, particleConfig } from "../themes/MainApp";
import "../themes/MainApp.css";

export class MainApp extends Component {
  constructor(props) {
    super(props);
    this.state = {
      spotifyName: null,
      spotifyData: null,
      isIdentified: false,
      isLoading: true,
      introMsgs: ["Hello"],
      introMsg: "Hello",
      introMsgIndex: 0,
    };
  }

  async componentDidMount() {
    this.loop = setInterval(() => this.setIntroMsg(), 3000);
    const spotifyToken = this.props.Spotify.spot_token;

    if (spotifyToken !== "") {
      console.log("Authenticated!");
      const spotifyRequestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          spotify_token: spotifyToken,
        }),
      };

      let tokenReAuthAPI = spotifyFlaskBaseAPI + "/my_spotify_id";
      // let tokenReAuthPromise =
      fetch(tokenReAuthAPI, spotifyRequestOptions)
        .then((response) => response.json())
        .then((data) =>
          this.setState({
            spotifyName: data["user"]["spotifyName"],
            isIdentified: true,
            introMsgs: [
              // data["user"]["spotifyName"],
              "Welcome to your liked songs dashboard!",
              "Spotify has yet to offer a good comprehensive solution",
              "to bring power and data back to its users from the songs they listen to.",
              "This serves to act as a small tool to bridge that gap",
              "Enjoy!",
            ],
          })
        );
      let dataLoadingAPI = spotifyFlaskBaseAPI + "/my_spotify_data";
      // let dataLoadingPromise =
      fetch(dataLoadingAPI, spotifyRequestOptions)
        .then((response) => response.json())
        .then((data) =>
          this.setState({
            spotifyData: data["data"],
            isLoading: false,
          })
        );
    }
  }

  setIntroMsg() {
    let currentMsgIndex = this.state.introMsgIndex;
    let introMsgIndex =
      currentMsgIndex > this.state.introMsgs.length ? 0 : currentMsgIndex + 1;
    let introMsg = this.state.introMsgs[introMsgIndex];
    this.setState({ introMsg: introMsg, introMsgIndex: introMsgIndex });
  }

  componentWillUnmount() {
    clearInterval(this.loop);
  }

  render() {
    console.log(this.state);
    var isIdentified = this.state.isIdentified;
    var isLoading = this.state.isLoading;
    var spotifyName = this.state.spotifyName;
    var spotifyData = this.state.spotifyData;
    var introMsg = this.state.introMsg;

    return (
      <div className="mainAppContainer">
        <ThemeProvider>
          <Div
            top={introContainer.top}
            left={introContainer.left}
            pos={introContainer.position}
            transform={introContainer.transform}
            textAlign={introContainer.textAlign}
          >
            <TextTransition
              text={introMsg}
              className="introMsgText"
              springConfig={presets.wobbly}
              inline
            />
          </Div>
          <ParticlesBg type="custom" config={particleConfig} bg={particleBg} />
        </ThemeProvider>
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  ...state,
});

const mapDispatchToProps = (dispatch) => ({});

export default connect(mapStateToProps, mapDispatchToProps)(MainApp);

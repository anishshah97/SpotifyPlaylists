import { Button, Div, ThemeProvider } from "atomize";
import ParticlesBg from "particles-bg";
import React, { Component } from "react";
import { connect } from "react-redux";
import { storeSpotToken } from "../actions/Spotify";
import { loginButton, particleBg, particleConfig } from "../themes/Login";
import "../themes/Login.css";
import { defaultTheme } from "../themes/Spotify";

//Green color theme to match Spotify
// TODO: Properly define a color scheme, wrap around whole App
// TODO: Move styles to separate file

const spotAuthLink = `${process.env.REACT_APP_SPOT_AUTH_END}?client_id=${process.env.REACT_APP_SPOT_CLID}&redirect_uri=${process.env.REACT_APP_REDIRECT_URI}&scope=${process.env.REACT_APP_SPOT_SCOPES}&response_type=token&show_dialog=true`;

const hash = window.location.hash
  .substring(1)
  .split("&")
  .reduce(function (initial, item) {
    if (item) {
      var parts = item.split("=");
      initial[parts[0]] = decodeURIComponent(parts[1]);
    }
    return initial;
  }, {});
window.location.hash = "";

export class Login extends Component {
  componentDidMount() {
    //Read spotify token from window after redirect and store in redux
    let _token = hash.access_token;
    //If token exists store in redux so the spotify API can always reference
    if (_token) {
      this.props.storeSpotToken(hash.access_token);
    }
    console.log(particleConfig);
    console.log();
  }
  //TODO: Find a good way to unpack login button without explicitly defining attributes
  render() {
    return (
      <ThemeProvider theme={defaultTheme}>
        <div className="loginContainer">
          <Div
            top={loginButton.top}
            left={loginButton.left}
            pos={loginButton.position}
            transform={loginButton.transform}
          >
            <a href={spotAuthLink}>
              <Button
                onClick={storeSpotToken}
                shadow="3"
                hoverShadow="4"
                bg={defaultTheme.colors.green}
                m={{ r: "1rem" }}
              >
                Login to Spotify
              </Button>
            </a>
          </Div>
          <ParticlesBg type="custom" config={particleConfig} bg={particleBg} />
        </div>
      </ThemeProvider>
    );
  }
}

const mapStateToProps = (state) => ({
  ...state,
});

const mapDispatchToProps = (dispatch) => ({
  storeSpotToken: (spot_token) => dispatch(storeSpotToken(spot_token)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Login);

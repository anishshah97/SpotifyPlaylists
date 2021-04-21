import React, { Component } from "react";
import { connect } from "react-redux";
import Button from "@material-ui/core/Button";
import { createMuiTheme, ThemeProvider } from "@material-ui/core/styles";
import { green } from "@material-ui/core/colors";
import { storeSpotToken } from "../actions/Spotify";

//Green color theme to match Spotify
// TODO: Properly define a color scheme, wrap around whole App
// TODO: Move styles to separate file
const theme = createMuiTheme({
  palette: {
    primary: green,
  },
});

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
  }

  render() {
    return (
      <div>
        <ThemeProvider theme={theme}>
          <Button
            variant="contained"
            color="primary"
            href={spotAuthLink}
            onClick={storeSpotToken}
          >
            Login to Spotify
          </Button>
        </ThemeProvider>
      </div>
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

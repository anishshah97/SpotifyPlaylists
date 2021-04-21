import React, { Component } from "react";
import { connect } from "react-redux";
import logo from "../logo.svg";
import "./testPage.css";

var baseAPI = "http://localhost:5000";

export class TestPage extends Component {
  constructor(props) {
    super(props);
    this.state = {
      spotifyName: null,
    };
  }

  async componentDidMount() {
    const spotifyToken = this.props.Spotify.spot_token;
    if (spotifyToken !== "") {
      console.log("Authenticated!");
      const spotifyRequestOptions = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spotify_token: spotifyToken }),
      };
      fetch(baseAPI + "/spotify_me", spotifyRequestOptions)
        .then((response) => response.json())
        .then((data) => this.setState({ spotifyName: data["spotifyName"] }));
    }
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <p>{this.state.spotifyName}</p>
        </header>
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  ...state,
});

const mapDispatchToProps = (dispatch) => ({});

export default connect(mapStateToProps, mapDispatchToProps)(TestPage);

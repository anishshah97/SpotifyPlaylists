import { StyleReset } from "atomize";
import React, { Component } from "react";
import { connect } from "react-redux";
import Login from "./pages/Login";
import TestPage from "./pages/testPage.js"; //TODO: Rename testpage to app
import "./themes/App.css";

//TODO: Pass theme provider to App for consistent color scheme of material UI

export class App extends Component {
  render() {
    //Flag to check if the user has a token, if not send to login page to get token
    const { spot_authenticated } = this.props.Spotify;

    return (
      <>
        <StyleReset />
        <div>
          {!spot_authenticated ? <Login></Login> : <TestPage></TestPage>}
        </div>
      </>
    );
  }
}

const mapStateToProps = (state) => ({
  ...state,
});

export default connect(mapStateToProps)(App);

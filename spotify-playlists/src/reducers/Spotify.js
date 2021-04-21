export default (
  state = {
    //Auth
    spot_authenticated: false,
    spot_token: "",
  },
  action
) => {
  switch (action.type) {
    //Store Token
    case "STORE_SPOT_TOKEN":
      return Object.assign({}, state, {
        spot_token: action.spot_token,
        spot_authenticated: true,
      });

    default:
      return state;
  }
};

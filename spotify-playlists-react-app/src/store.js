import { applyMiddleware, createStore } from "redux";
//import promise from "redux-promise-middleware";
import { composeWithDevTools } from "redux-devtools-extension";
import logger from "redux-logger";
import thunk from "redux-thunk";
import rootReducer from "./reducers/rootReducer";

const composeEnhancers = composeWithDevTools({
  trace: true,
  traceLimit: 25,
});

export default function configureStore() {
  return createStore(
    rootReducer,
    composeEnhancers(applyMiddleware(thunk, logger))
  );
}

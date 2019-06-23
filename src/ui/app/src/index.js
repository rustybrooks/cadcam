import React from "react";
import ReactDOM from "react-dom";

import { createBrowserHistory } from 'history'

import App from './App'

// Create a history of your choosing (we're using a browser history in this case)
const history = createBrowserHistory();

ReactDOM.render(
  <App/>,
  document.getElementById("root")
)

module.hot.accept();



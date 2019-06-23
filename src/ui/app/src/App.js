import React, { Component } from 'react'
import createStore from './global-store/createStore'

import { BrowserRouter, Route } from 'react-router-dom'
import Home from './components/Home'



/*
*/



class App extends Component {


  render() {
    return (
      <BrowserRouter basename={process.env.PUBLIC_URL}>
        <div>
          <Route exact path="/" component={Home} />
        </div>
      </BrowserRouter>
    )
  }
}

const initialValue = {
}

const config = {}

export default createStore(App, initialValue, config)
// export default App



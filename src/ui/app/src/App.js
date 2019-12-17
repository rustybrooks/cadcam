import React, { Component } from 'react'
import createStore from './global-store/createStore'
import { BrowserRouter, Route } from 'react-router-dom'


import { BASE_URL } from './constants/api'
import fetchFrameworks from './framework_client'
import Home from './components/Home'
import Projects from './components/Projects'
import Project from './components/project/Project'
import Header from './components/Header'
import Machines from './components/Machines'
import Tools from './components/Machines'



class App extends Component {
  updateFrameworks() {
    const { store } = this.props

    fetchFrameworks(BASE_URL, '/api', store).then(data => {
      store.set('frameworks', data)
    })
  }

  componentDidMount() {
    this.updateFrameworks()
  }

  render() {
    let { store } = this.props
    if (store.get('frameworks') === null) {
     return <div>Loading App</div>
    }

    return (
      <BrowserRouter basename={process.env.PUBLIC_URL}>
        <div>
          <Header/>
          <Route exact path="/" component={Home} />
          <Route exact path="/projects/:username" component={Projects} />
          <Route exact path="/projects/:username/create" component={Projects} />
          <Route exact path="/projects/:username/:project_key/:tab" component={Project} />
          <Route exact path="/machines/:username" component={Machines} />
          <Route exact path="/tools/:username" component={Tools} />
        </div>
      </BrowserRouter>
    )
  }
}

const initialValue = {
  'frameworks': null,
  'login-widget': null,
  'user': null,
}

const config = {}

export default createStore(App, initialValue, config)



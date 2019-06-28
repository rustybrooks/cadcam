import React, { Component } from 'react'
import createStore from './global-store/createStore'
import { BrowserRouter, Route } from 'react-router-dom'


import { BASE_URL } from './constants/api'
import fetchFrameworks from './framework_client'
import Home from './components/Home'
import Projects from './components/Projects'
import Project from './components/Project'
import Header from './components/Header'




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
     return <div>Loading</div>
    }

    return (
      <BrowserRouter basename={process.env.PUBLIC_URL}>
        <div>
          <Header/>
          <Route exact path="/" component={Home} />
          <Route exact path="/projects" component={Projects} />
          <Route exact path="/projects/create" component={Projects} />
          <Route exact path="/projects/:project_key/" component={Project} />*/}
        </div>
      </BrowserRouter>
    )
  }
}

const initialValue = {
  'frameworks': null,
  'login-widget': null,
}

const config = {}

export default createStore(App, initialValue, config)



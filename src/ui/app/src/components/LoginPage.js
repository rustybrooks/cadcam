import React from 'react'

import ReactSignupLoginComponent from './login/ReactSignupLoginComponent'
import { withStore } from '../global-store'


class LoginPage extends React.Component {
  signupWasClickedCallback = (data) => {
    // console.log(data);
    alert('Signup callback, see log on the console to see the data.')
  }

  loginWasClickedCallback = (data) => {
    const { store } = this.props

    // console.log(data);
    let fw = store.get('frameworks')
    let val = fw.UserApi.api_login({'username': data.username, 'password': data.password})
    val.then(data => localStorage.setItem('api-key', data))
    store.get('login-widget').toggleDrawer(false)
  }

  recoverPasswordWasClickedCallback = (data) => {
    // console.log(data);
    alert('Recover password callback, see log on the console to see the data.')
  }

  render() {
    return (
      <div>
        <ReactSignupLoginComponent
          handleSignup={this.signupWasClickedCallback}
          handleLogin={this.loginWasClickedCallback}
          handleRecoverPassword={this.recoverPasswordWasClickedCallback}
        />
      </div>
    )
  }
}

export default withStore(LoginPage)
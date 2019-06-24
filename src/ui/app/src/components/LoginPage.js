import React from 'react'

import ReactSignupLoginComponent from 'react-signup-login-component'

class LoginPage extends React.Component {
  signupWasClickedCallback = (data) => {
    console.log(data);
    alert('Signup callback, see log on the console to see the data.')
  }

  loginWasClickedCallback = (data) => {
    console.log(data);
    alert('Login callback, see log on the console to see the data.')
  }

  recoverPasswordWasClickedCallback = (data) => {
    console.log(data);
    alert('Recover password callback, see log on the console to see the data.')
  }

  render() {
    return (
      <div>
        <ReactSignupLoginComponent
          title="My awesome company"
          handleSignup={this.signupWasClickedCallback}
          handleLogin={this.loginWasClickedCallback}
          handleRecoverPassword={this.recoverPasswordWasClickedCallback}
        />
      </div>
    )
  }
}

export default LoginPage
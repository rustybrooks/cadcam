import React, { useState } from 'react'

import { withStore } from '../global-store'
import { withStyles } from '@material-ui/core/styles'

import * as material from '@material-ui/core'

const style = theme => ({
  root: {
    maxWidth: 600,
    minWidth: 400,
    "float": 'right',
  },

  formControl: {
    margin: theme.spacing(1),
    minWidth: 120,
  },

  button: {
    margin: theme.spacing(1),
  },
})

function LoginPage({store, classes}) {
  const [tab, setTab] = useState('login');
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [password2, setPassword2] = useState('')
  const [errors, setErrors] = useState({})

  const handleTabChange = (event, newTab) => {
    setTab(newTab)
  }

  const doCancel = () => {
      store.get('login-widget').closeDrawer()
  }

  const doLogin = async () => {
    let fw = store.get('frameworks')
    let result = await fw.UserApi.api_login({'username': username, 'password': password})
    if (result.status === 403) {
      localStorage.setItem('api-key', null)
      setErrors({...errors, 'password': 'Error logging in'})
    } else {
      setErrors({})
      localStorage.setItem('api-key', result)
      store.get('login-widget').closeDrawer()
      store.get('login-widget').updateUser()
    }
  }

  const doSignup = async () => {
    let fw = store.get('frameworks')
    let result = await fw.UserApi.signup({
      'username': username, 'email': email,
      'password': password, 'password2': password2
    })
    if (result.status === 400) {
      setErrors(result.details)
    } else {
      setErrors({})
      localStorage.setItem('api-key', result)
      store.get('login-widget').closeDrawer()
      store.get('login-widget').updateUser()
    }
  }

  return <div className={classes.root}>
    <material.Tabs value={tab} onChange={handleTabChange}>
      <material.Tab label="Login" value="login"/>
      <material.Tab label="Signup" value="signup"/>
    </material.Tabs>

    <material.Box component="div" display={tab === 'signup' ? "block" : "none"}>
      <material.FormGroup>

        <material.FormControl className={classes.formControl}>
          <material.TextField error={Boolean(errors.username)} helperText={errors.username} id="susername" label="Username" onChange={event => setUsername(event.target.value)} />
        </material.FormControl>

        <material.FormControl className={classes.formControl}>
          <material.TextField error={Boolean(errors.email)} helperText={errors.username} id="semail" label="Email" onChange={event => setEmail(event.target.value)} />
        </material.FormControl>

        <material.FormControl className={classes.formControl}>
          <material.TextField error={Boolean(errors.password)} helperText={errors.password} id="spassword" label="Password" type="password" onChange={event => setPassword(event.target.value)} />
        </material.FormControl>

        <material.FormControl className={classes.formControl}>
          <material.TextField error={Boolean(errors.password2)} helperText={errors.password2} id="spassword2" label="Confirm Password" type="password" onChange={event => setPassword2(event.target.value)} />
        </material.FormControl>

      </material.FormGroup>

      <material.Button className={classes.button} onClick={doCancel} variant='contained'>Cancel</material.Button>
      <material.Button className={classes.button} onClick={doSignup} variant='contained' color='primary'>Sign up</material.Button>
    </material.Box>

    <material.Box component="div" display={tab === 'login' ? "block" : "none"}>
      <material.FormGroup>

        <material.FormControl className={classes.formControl}>
          <material.TextField error={Boolean(errors.username)} helperText={errors.username} id="username" label="Username" onChange={event => setUsername(event.target.value)} />
        </material.FormControl>

        <material.FormControl className={classes.formControl}>
          <material.TextField error={Boolean(errors.password)} helperText={errors.password} id="password" label="Password" type="password" onChange={event => setPassword(event.target.value)} />
        </material.FormControl>

      </material.FormGroup>

      <material.Button className={classes.button} onClick={doCancel} variant='contained'>Cancel</material.Button>
      <material.Button className={classes.button} onClick={doLogin} variant='contained' color='primary'>Login</material.Button>
    </material.Box>

  </div>
}


export default withStyles(style)(withStore(LoginPage, ['login-widget']))

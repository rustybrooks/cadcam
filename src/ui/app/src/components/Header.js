import React from 'react'
import { withStyles } from '@material-ui/core/styles'
import Toolbar from '@material-ui/core/Toolbar'
import Button from '@material-ui/core/Button'
import { Link } from 'react-router-dom'
import AppBar from '@material-ui/core/AppBar'
import Drawer from '@material-ui/core/Drawer'
import { makeStyles } from '@material-ui/core/styles';
import * as material from '@material-ui/core'
import { withRouter } from 'react-router'

import { withStore } from '../global-store'
import LoginPage from './LoginPage'

const style = theme => ({
  root: {
    flexGrow: 1,
  },
  menuButton: {
    marginRight: theme.spacing(2),
  },
  title: {
    flexGrow: 1,
  },
})

class Header extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      'login-open': false,
      'anchorEl': null,
    }

    this.openDrawer = this.openDrawer.bind(this)
    this.closeDrawer = this.closeDrawer.bind(this)
    this.logout = this.logout.bind(this)
  }

  async updateUser() {
    const { store } = this.props
    let fw = store.get('frameworks')
    if (fw === null || fw === undefined) return

    const data = await fw.UserApi.user()
    if (data.status === 403) {
      store.set('user', null)
    } else {
      store.set('user', data)
    }
  }

  closeDrawer() {
    this.setState({...this.state, 'login-open': false});
  }

  openDrawer() {
    this.setState({...this.state, 'login-open': true});
  }

  logout = () => {
    localStorage.setItem('api-key', null)
    const { store, history } = this.props
    store.set('user', null)
    history.push('/')
  }

  componentDidMount() {
    const { store } = this.props
    store.set('login-widget', this)
    this.updateUser()
  }

  componentDidUpdate(prevProps, prevState) {
    //console.log("update", this.props)
  }

  render() {
    const { store, classes } = this.props

    const user = store.get('user')

    return (
      <div className={classes.root}>
        <AppBar position="static">
          <Toolbar>
            <Button color="inherit" component={Link} to="/">Home</Button>
            {user ? <Button color="inherit" component={Link} to={"/projects/" + user.username}>Projects</Button> : <div></div>}
            {user ? <Button color="inherit" component={Link} to={"/machines/" + user.username}>Machines</Button> : <div></div>}
            {user ? <Button color="inherit" component={Link} to={"/tools/" + user.username}>Tools</Button> : <div></div>}
            <div className={classes.title}> </div>

            {user ? <div>
              <material.Typography>
                ({user.username})
                <Button color="inherit" onClick={this.logout}>Logout</Button>
              </material.Typography>
            </div> : <Button color="inherit" onClick={this.openDrawer}>Login / Sign up</Button>
            }

            </Toolbar>
        </AppBar>
        <Drawer anchor="top" open={this.state['login-open']} onClose={this.closeDrawer}>
          <div role="presentation">
            <LoginPage/>
          </div>
        </Drawer>
      </div>
    )
  }
}

export default withRouter(withStore(withStyles(style)(Header), ['user']))

import React from 'react'
import { withStyles } from '@material-ui/core/styles'
import Toolbar from '@material-ui/core/Toolbar'
import Button from '@material-ui/core/Button'
import { Link } from 'react-router-dom'
import AppBar from '@material-ui/core/AppBar'
import Drawer from '@material-ui/core/Drawer'
import { makeStyles } from '@material-ui/core/styles';

import { withStore } from '../global-store'
import LoginPage from './LoginPage'

const style = theme => ({
  root: {
    flexGrow: 1,
  },
  menuButton: {
    // marginRight: theme.spacing(2),
  },
  title: {
    flexGrow: 1,
  },
})

class Header extends React.Component {
  state = {
    'login-open': false,
    'anchorEl': null,
  }

  toggleDrawerEvent(open) {
    return event => {
      if (event.type === 'keydown' && (event.key !== 'Escape')) {
        return;
      }
      this.toggleDrawer(open)
    }
  };

  toggleDrawer(open) {
      this.setState({...this.state, 'login-open': open});
  }

  componentDidMount() {
    const { store } = this.props
    store.set('login-widget', this)
  }

  render() {
    const { classes } = this.props
    return (
      <div className={classes.root}>
        <AppBar position="static">
          <Toolbar>
            <Button color="inherit" component={Link} to="/">Home</Button>
            <Button color="inherit" component={Link} to="/projects/me">Projects</Button>
          </Toolbar>
        </AppBar>
        <Drawer anchor="top" open={this.state['login-open']} onClose={this.toggleDrawerEvent(false)}>
          <div
              role="presentation"
            >
            <LoginPage/>
          </div>
        </Drawer>
      </div>
    )
  }
}

export default withStore(withStyles(style)(Header))
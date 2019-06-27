import React from 'react'
import { withStyles } from '@material-ui/core/styles'
import Toolbar from '@material-ui/core/Toolbar'
import IconButton from '@material-ui/core/IconButton'
import { Link } from 'react-router-dom'
import AppBar from '@material-ui/core/AppBar'
import Typography from '@material-ui/core/Typography';
import MenuIcon from '@material-ui/icons/Menu';

import MenuItem from '@material-ui/core/MenuItem';
import { makeStyles } from '@material-ui/core/styles';


import Menu from '@material-ui/core/Menu';

import fetchFrameworks from '../framework_client'
import { withStore } from '../global-store'
import LoginPage from './LoginPage'

import { BASE_URL } from '../constants/api'

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

  handleClick(event) {
    this.setState({...this.state, anchorEl: event.currentTarget})
  }

  handleClose() {
    this.setState({...this.state, anchorEl: null})
  }

  toggleDrawer(open) {
    return event => {
      if (event.type === 'keydown' && (event.key !== 'Escape')) {
        return;
      }

      console.log("Setting state to", open)
      this.setState({...this.state, 'login-open': open});
    }
  };

  updateFrameworks() {
    const { store } = this.props
    store.set('frameworks', null)

    fetchFrameworks(BASE_URL, '/api').then(data => {
      console.log(data)
      store.set('frameworks', data)
    })
  }

  componentDidMount() {
    this.updateFrameworks()
  }

  render() {
    const { classes } = this.props
    return (
      <div className={classes.root}>
        <AppBar position="static">
          <Toolbar>
            <IconButton
              edge="start"
              className={classes.menuButton}
              color="inherit"
              aria-label="Menu"
              onClick={this.handleClick}
            >
              <MenuIcon/>
            </IconButton>
            <Menu
              id="simple-menu"
              anchorEl={this.state.anchorEl}
              keepMounted
              open={Boolean(this.state.anchorEl)}
              onClose={this.handleClose}
            >
              <MenuItem onClick={this.handleClose}>Profile</MenuItem>
              <MenuItem onClick={this.handleClose}>My account</MenuItem>
              <MenuItem onClick={this.handleClose}>Logout</MenuItem>
            </Menu>
            <Typography variant="h6" className={classes.title}>
              News
            </Typography>
            {/*<Button color="inherit" onClick={this.toggleDrawer(true)}>Login</Button>*/}
          </Toolbar>
        </AppBar>
        {/*<Drawer anchor="top" open={this.state['login-open']} onClose={this.toggleDrawer(false)}>*/}
          {/*<div*/}
              {/*role="presentation"*/}
              {/*// onClick={this.toggleDrawer(false)}*/}
              {/*// onKeyDown={this.toggleDrawer(false)}*/}
            {/*>*/}
            {/*<LoginPage/>*/}
          {/*</div>*/}
        {/*</Drawer>*/}
      </div>
    )
  }
}

export default withStore(withStyles(style)(Header))
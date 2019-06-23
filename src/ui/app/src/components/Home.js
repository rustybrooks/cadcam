import React from 'react'
import Paper from '@material-ui/core/Paper'
import { withStyles } from '@material-ui/core/styles'
import Button from '@material-ui/core/Button'
import { Link } from 'react-router-dom'
import fetchFrameworks from '../framework_client'
import { withStore } from '../global-store'

import { BASE_URL } from '../constants/api'

const style = theme => ({
  paper: {
    padding: theme.spacing.unit
  },
  badgeLink: {
    margin: 2
  },
  cookies: {
    display: 'flex',
    alignItems: 'center'
  },
  button: {
    color: `${theme.palette.primary.contrastText}!important`,
    margin: 2
  }
})

class Home extends React.Component {
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
      <Paper className={classes.paper}>
      </Paper>
    )
  }
}

export default withStore(withStyles(style)(Home))

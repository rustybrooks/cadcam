import React from 'react'
import Paper from '@material-ui/core/Paper'
import { withStyles } from '@material-ui/core/styles'
import { withStore } from '../global-store'

const style = theme => ({
  'paper': {

  }
});


class Home extends React.Component {
  render() {
    const { classes } = this.props

    return (
     <div>Hi</div>
    )
  }
}

export default withStore(withStyles(style)(Home))




import React from 'react'

import { withRouter } from 'react-router'
import { withStore } from '../global-store'
import { withStyles } from '@material-ui/core/styles'


const style = theme => ({
  root: {
    marginTop: theme.spacing(1),
  },
})


class Machines extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
    }

  }

  render() {
    const { store, classes } = this.props
    return <div>Nothing yet</div>
  }

}

export default withRouter(withStore(withStyles(style)(Machines)))







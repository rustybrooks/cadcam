import React from 'react'
import TextField from '@material-ui/core/TextField';
import DialogContentText from '@material-ui/core/DialogContentText';

import { withStyles } from '@material-ui/core/styles'


import { withStore } from '../global-store'

const style = theme => ({
})

class Project extends React.Component {
  render() {
    return <div>
      It's a project
    </div>
  }
}

export default withStore(withStyles(style)(Project))
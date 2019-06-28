import React from 'react'
import TextField from '@material-ui/core/TextField';
import DialogContentText from '@material-ui/core/DialogContentText';

import { withStyles } from '@material-ui/core/styles'


import { withStore } from '../global-store'

const style = theme => ({
})

class CreateProject extends React.Component {
  render() {
    return <div>
        <DialogContentText>
          To subscribe to this website, please enter your email address here. We will send updates
          occasionally.
        </DialogContentText>
        <TextField
          autoFocus
          margin="dense"
          id="name"
          label="Email Address"
          type="email"
          fullWidth
        />
    </div>
  }
}

export default withStore(withStyles(style)(CreateProject))
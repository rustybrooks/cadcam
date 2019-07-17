import React from 'react'
import TextField from '@material-ui/core/TextField';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogActions from '@material-ui/core/DialogActions';
import Button from '@material-ui/core/Button'

import { withStyles } from '@material-ui/core/styles'
import { withRouter } from 'react-router'


import { withStore } from '../global-store'

const style = theme => ({
})

class CreateProject extends React.Component {
  constructor(props) {
    super(props)

    this.handleCreate = this.handleCreate.bind(this)
    this.handleNameChange = this.handleNameChange.bind(this)
    this.handleProjectKeyChange = this.handleProjectKeyChange.bind(this)

    this.state = {
      'name': '',
      'project_key': '',
    }
  }

  handleCreate() {
    console.log("closing")
    const { store } = this.props
    const fw = store.get('frameworks')
    fw.ProjectsApi.create({project_key: this.state.project_key, name: this.state.name}).then(data => this.props.history.push('/projects/me/' + this.state.project_key))
  }

  handleNameChange = event => {
    let newname = event.target.value.toLowerCase().split('')
    let achar = 'a'.charCodeAt()
    let zchar = 'z'.charCodeAt()
    let zerochar = '0'.charCodeAt()
    let ninechar = '9'.charCodeAt()
    newname = newname.map(c => {
      return (
        (c.charCodeAt() > achar && c.charCodeAt() < zchar) ||
        (c.charCodeAt() > zerochar && c.charCodeAt() < ninechar)
      ) ? c : '-'
    })
    newname = newname.join('').replace(/\-+/g, '-').replace(/^\-+|\-+$/g, '');
    this.setState({...this.state, project_key: newname, name: event.target.value})
  };

  handleProjectKeyChange = event => {
    this.setState({...this.state, project_key: event.target.value})
  };

  render() {
    return <div>
        <DialogContentText>
          Create a new CAM project
        </DialogContentText>
        <TextField
          margin="dense" id="name" label="Project Key" type="project_key" fullWidth
          onChange={this.handleProjectKeyChange} value={this.state.project_key}
        />
        <TextField
          autoFocus margin="dense" id="name" label="Project Name" type="name" fullWidth
          onChange={this.handleNameChange} value={this.state.name}
        />

        <DialogActions>
          <Button onClick={this.props.handleClose} color="primary">
            Cancel
          </Button>
          <Button onClick={this.handleCreate} color="primary">
            Create
          </Button>
        </DialogActions>
    </div>
  }
}

export default withRouter(withStore(withStyles(style)(CreateProject)))

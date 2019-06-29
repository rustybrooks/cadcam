import React from 'react'
import * as material from '@material-ui/core'

import { withStyles } from '@material-ui/core/styles'
import { withRouter } from 'react-router'

import { withStore } from '../global-store'
import DropzoneArea from './dropzone/DropZoneArea'


const style = theme => ({
})



class PCBRender extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      img: ''
    };
  };

  componentDidUpdate(prevProps, prevState, snapshot) {
    if (prevProps == this.props) return

    console.log('update', this.props)
    if (this.props.project_key === null) {
      return
    }

    let fw = this.props.store.get('frameworks')
    fw.PCBApi.render({project_key: this.props.project_key, 'side': this.props.side}).then(
      data => this.setState({img: 'data:image/jpeg;base64,' + data})
    )
  }

  render() {
    if (this.props.project_key === null) {
      return <div></div>
    }

    if (!this.state.img.length) {
      return <div></div>
    }

    return <img src={this.state.img}/>

  }
}


class Project extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      uploadModal: false,
      files: [],
      project_key: null,
    }

    // This binding is necessary to make `this` work in the callback
    this.handleClose = this.handleClose.bind(this)
    this.handleOpen = this.handleOpen.bind(this)
    this.handleChange = this.handleChange.bind(this)
    this.handleUpload = this.handleUpload.bind(this)
  }

  handleClose() {
    this.setState({...this.state, uploadModal: false})
  }

  handleOpen() {
    this.setState({...this.state, uploadModal: true})
  }

  handleChange(files){
    console.log(files)
    this.setState({...this.state, files: files});
  }

  handleUpload() {
    let { store } = this.props
    let fw = store.get('frameworks')

    this.state.files.map(file => {
      var formData = new FormData();
      formData.append('file', file);
      formData.append('project_key', this.state.project_key)
      fw.ProjectsApi.upload_file(formData).then(data => console.log(file, data))
    })
  }

  componentDidMount() {
    this.onRouteChanged()
  }

  componentDidUpdate(prevProps) {
    if (this.props.location.pathname !== prevProps.location.pathname) {
      this.onRouteChanged()
    }
  }

  onRouteChanged() {
    console.log('route', this.props.match.params)
    this.setState({...this.state, project_key: this.props.match.params.project_key})
  }

  render() {
    const { store, classes } = this.props
    console.log('render', this.state)

    return <material.Paper className={classes.paper}>
      <table>
        <tbody>
          <tr>
            <td colSpan="2">
              <material.Button onClick={this.handleOpen}>Upload Gerber File(s)</material.Button>
            </td>
          </tr>
          <tr>
            <td>
              <PCBRender project_key={this.state.project_key} side='top'/>
            </td>
            <td>
              <PCBRender project_key={this.state.project_key} side='bottom'/>

            </td>
          </tr>
        </tbody>
      </table>


      <material.Dialog open={this.state.uploadModal} onClose={this.handleClose} aria-labelledby="form-dialog-title">
        <material.DialogTitle id="form-dialog-title">Upload File(s)</material.DialogTitle>
        <material.DialogContent>
          <DropzoneArea
            onChange={this.handleChange}
            onSave={this.handleSave}
            dropzoneText="Drag and drop gerber files here or click"
            maxFileSize={1024*1024*10}
            filesLimit={20}
          />
          <br/><br/>
          <material.Button onClick={this.handleUpload}>Upload</material.Button>
        </material.DialogContent>
      </material.Dialog>

    </material.Paper>
  }
}

PCBRender = withStore(PCBRender)

export default withRouter(withStore(withStyles(style)(Project)))
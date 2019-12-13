import React from 'react'
import * as material from '@material-ui/core'
import * as moment from 'moment'

import { withStyles } from '@material-ui/core/styles'

import { Switch, Route, Link, BrowserRouter, Redirect } from "react-router-dom";


import { withStore } from '../../global-store'
import DropzoneArea from '../dropzone/DropZoneArea'

import { Status } from '../../framework_client'

import ProjectDetails from './ProjectDetails'
import ProjectRender from './ProjectRender'
import ProjectCAM from './ProjectCAM'



const style = theme => ({
  tab: {
  },
})


class Project extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      uploadModal: false,
      files: [],
      project_key: null,
      project: null,
      username: null,
      // tabValue: 0,
    }

    // This binding is necessary to make `this` work in the callback
    this.handleClose = this.handleClose.bind(this)
    this.handleOpen = this.handleOpen.bind(this)
    this.handleChange = this.handleChange.bind(this)
    this.handleUpload = this.handleUpload.bind(this)
  }

  handleClose() {
    this.setState({uploadModal: false})
  }

  handleOpen() {
    this.setState({uploadModal: true})
  }

  handleChange(files) {
    this.setState({files: files})
  }

  handleSave() {
    console.log("save handled")
  }

  handleUpload() {
    let { store } = this.props
    let fw = store.get('frameworks')

    this.state.files.map(file => {
      let formData = new FormData()
      formData.append('file', file)
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
    const params = this.props.match.params
    const { username, project_key, tab } = params

    let { store } = this.props
    let fw = store.get('frameworks')
    fw.ProjectsApi.project({project_key: project_key, username: username}).then(data => {
      this.setState({
        project_key: project_key,
        username: username,
        tab: tab ? tab : 'details',
        project: data,
      })
    })
  }

  render() {
    const { classes } = this.props
    const { project, tab, username } = this.state


    if (project === null) {
      return <div>Loading</div>
    }

    if (project.status === 404) {
      return <div>{project.details}</div>
    } else if (project instanceof Status) {
      return <div>Error: project.details</div>
    }

    const urlbase = '/projects/' + username + '/' + project.project_key

    return <material.Paper className={classes.paper}>
      <material.Tabs value={location.pathname} >
        <material.Tab label="Summary" value={urlbase} component={Link} to={urlbase}>
        </material.Tab>

        <material.Tab label="PCB Renders" value={urlbase + '/render'} component={Link} to={urlbase + '/render'}>
        </material.Tab>

        <material.Tab label="CAM" value={urlbase + '/cam'} component={Link} to={urlbase + '/cam'}>
        </material.Tab>
      </material.Tabs>

      <material.Box component="div" display={tab === 'details' ? "block" : "none"}>
        <ProjectDetails project={project} handleOpen={this.handleOpen}/>
      </material.Box>

      <material.Box component="div" display={tab === 'render' ? "block" : "none"}>
        <ProjectRender project={project} />
      </material.Box>

      <material.Box component="div" display={tab === 'cam' ? "block" : "none"}>
        <ProjectCAM project={project} />
      </material.Box>

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
          <material.Button variant='outlined' onClick={this.handleClose}>Close</material.Button>
          <material.Button variant='outlined' onClick={this.handleUpload}>Upload</material.Button>
        </material.DialogContent>
      </material.Dialog>

    </material.Paper>
  }
}

export default withStore(withStyles(style)(Project))

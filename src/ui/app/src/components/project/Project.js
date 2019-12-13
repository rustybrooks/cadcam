import React from 'react'
import * as material from '@material-ui/core'
import * as moment from 'moment'

import { withStyles } from '@material-ui/core/styles'

import { Switch, Route, Link, BrowserRouter, Redirect } from "react-router-dom";


import { withStore } from '../../global-store'
import DropzoneArea from '../dropzone/DropZoneArea'

import { Status } from '../../framework_client'

import CAMRender from './CAMRender'
import PCBRender from './PCBRender'




const style = theme => ({
  tab: {
  },
})

const detailsStyle = theme => ({

})


const renderStyle = theme => ({
  forms: {
  },
  formControl: {
    margin: theme.spacing(3),
  },

})

const camStyle = theme => ({

})



class ProjectRender extends React.Component {
  render() {
    const { project, classes } = this.props

    return <div>
      <table border="0" cellSpacing="2">
        <tbody>
          <tr>
            <td valign="top">
              <PCBRender store={this.props.store} project_key={project.project_key} username={project.username} side='top'/>
            </td>
            <td valign="top">
              <PCBRender store={this.props.store} project_key={project.project_key} username={project.username} side='bottom'/>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  }
}

class ProjectCAM extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      'cut_depth': [0.005, 'in'],
      'trace_separation': [0.015, 'in'],
      'zprobe_type': 'none',
      'border': [0, 'in'],
      'thickness': [.067, 'in'],
      'panelx': 1,
      'panely': 1,
      'posts': 'none',
      'two_sided': false,
    }
  }

  handleChange = name => event => {
    this.setState({
      ...this.state,
      [name]: event.target.value,
    });
  };

  render() {
    const { classes, project } = this.props

    return <div className={classes.root}>
      <div className={classes.forms}>
        <material.FormGroup row>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="zprobe-type-label">Z Probe Type</material.InputLabel>
            <material.Select
              labelId="trace_depth-label" id="zprobe-type-select"
              value={this.state.zprobe_type} onChange={this.handleChange('zprobe_type').bind(this)}
            >
              <material.MenuItem value='none'>None</material.MenuItem>
              <material.MenuItem value='auto'>Auto</material.MenuItem>
            </material.Select>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="trace-depth-label">Cut depth</material.InputLabel>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="trace-depth-label">Trace separation</material.InputLabel>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="border-label">Border</material.InputLabel>
          </material.FormControl>

        </material.FormGroup>

        <material.FormGroup row>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="panel-x-label">Z Probe Type</material.InputLabel>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="panel-y-label">Cut depth</material.InputLabel>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="two-sided-label">Two sided</material.InputLabel>
          </material.FormControl>

        </material.FormGroup>

      </div>

      <table border={0} cellSpacing={2}>
        <tbody>
          <tr>
            <td valign="top">
              <CAMRender
                store={this.props.store} project_key={project.project_key} username={project.username} side='top'
                zprobe_type={this.state.zprobe_type}
              />
            </td>
            <td valign="top">
              {/*<CAMRender store={this.props.store} project_key={project.project_key} username={project.username} side='bottom'/>*/}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  }
}




class ProjectDetails extends React.Component {
  render () {
    const { project, classes } = this.props

    return <div>
      <table border={1} cellSpacing={0} cellPadding={5}>
        <tbody>
        <tr>
          <th align="left">Project Key</th><td colSpan={3}>{project.project_key}</td>
        </tr>

        <tr>
          <th align="left">Project Name</th><td colSpan={3}>{project.name}</td>
        </tr>

        <tr>
          <th align="left">Owner</th><td colSpan={3}>{project.username}</td>
        </tr>

        <tr>
          <th align="left">Created</th><td>{moment.duration(project.created_ago, 'seconds').humanize()}</td>
          <th align="left">Updated</th><td>{moment.duration(project.modified_ago, 'seconds').humanize()}</td>
        </tr>

        <tr>
          <th colSpan={4} align="left">
            Files
          </th>
        </tr>
        <tr>
          <td colSpan={4}>
          <material.Button variant='outlined' onClick={this.props.handleOpen} color="primary">
            Add Files
          </material.Button>
          </td>
        </tr>
        {
          project.files.map(f => {
            return <tr key={f.project_file_id}>
              <td colSpan={3}>{f.file_name}</td>
              <td colSpan={1}>{moment.duration(f.uploaded_ago, 'seconds').humanize()}</td>
              <td>
                <material.Button onClick={() => {window.location.href = 'http://localhost:5000/api/projects/download_file/' + project.project_key + '-' + f.file_name + '?project_file_id=' + f.project_file_id; return null;}} variant='outlined' color="primary">
                  Download
                </material.Button>
              </td>
            </tr>
          })
        }
        </tbody>
      </table>
    </div>
  }
}


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

  handleChange(files){
    this.setState({files: files})
  }

  handleUpload() {
    let { store } = this.props
    let fw = store.get('frameworks')

    this.state.files.map(file => {
      var formData = new FormData()
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

ProjectDetails = withStore(withStyles(detailsStyle)(ProjectDetails))
ProjectRender = withStore(withStyles(renderStyle)(ProjectRender))
ProjectCAM = withStore(withStyles(camStyle)(ProjectCAM))

export default withStore(withStyles(style)(Project))

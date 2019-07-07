import React from 'react'
import ReactLoading from 'react-loading'
import * as material from '@material-ui/core'
import * as moment from 'moment'

import { withStyles } from '@material-ui/core/styles'
import { withRouter } from 'react-router'

import { Switch, Route, Link, BrowserRouter, Redirect } from "react-router-dom";


import { withStore } from '../global-store'
import DropzoneArea from './dropzone/DropZoneArea'

import { Status } from '../framework_client'


const pcbrenderStyle = theme => ({
  'loadingDiv': {
    height: '600px',
    width: '600px',
    display: 'flex',
    'align-items': 'center',
    'justify-content': 'center',
  },
})


const style = theme => ({
  tab: {
  },
})

const detailsStyle = theme => ({

})


const renderStyle = theme => ({
  forms: {
    display: 'flex',
  },
  formControl: {
    margin: theme.spacing(3),
  },

})

const camStyle = theme => ({

})



class PCBRender extends React.Component {
  loading_color = '#555888'

  constructor(props) {
    super(props)
    this.state = {
      img: '',
      layers: {
        copper: true,
        'solder-mask': false,
        'silk-screen': false,
        drill: false,
      }
    }

    // This binding is necessary to make `this` work in the callback
    this.handleCheckChange = this.handleCheckChange.bind(this)
  }

  handleCheckChange = name => event => {
    console.log("handleCheckChange")
    this.setState({layers: {...this.state.layers, [name]: event.target.checked }})
    // this.updateImage()
  }

  componentDidMount() {
    console.log("Mount")
    this.updateImage()
  }

  componentDidUpdate(prevProps, prevState) {
    console.log(this.props, prevProps)
    if (this.state.layers == prevState.layers) return
    this.updateImage()
  }

  async updateImage() {
    const fw = this.props.store.get('frameworks')
    const layers = Object.keys(this.state.layers).filter(key => this.state.layers[key])
    this.setState({img: ''})
    const data = await fw.PCBApi.render_svg({
      project_key: this.props.project_key,
      username: this.props.username,
      side: this.props.side,
      layers: layers.join(),
    })
    this.setState({img: 'data:image/svg+xml;base64,' + data})

  }

  render() {
    const { classes } = this.props
    const { copper, drill } = this.state.layers
    const solderMask = this.state['solder-mask']
    const silkScreen = this.state['silk-screen']


    return (
      <div className={classes.forms}>
        <material.FormGroup row>
          <material.FormControlLabel
            control={<material.Checkbox checked={copper} onChange={this.handleCheckChange('copper')} value="copper" />}
            label="Copper"
          />
          <material.FormControlLabel
            control={<material.Checkbox checked={solderMask} onChange={this.handleCheckChange('solder-mask')} value="solderMask" />}
            label="Solder Mask"
          />
          <material.FormControlLabel
            control={<material.Checkbox checked={silkScreen} onChange={this.handleCheckChange('silk-screen')} value="silkScreen" />}
            label="Silk Screen"
          />
          <material.FormControlLabel
            control={<material.Checkbox checked={drill} onChange={this.handleCheckChange('drill')} value="drill" />}
            label="Drill"
          />
        </material.FormGroup>
        {
          (!this.state.img.length)
            ? <div className={classes.loadingDiv}><ReactLoading type={'spinningBubbles'} color={this.loading_color} height={50} width={50} /></div>
            : <img src={this.state.img}/>
        }
      </div>
    )
  }

}

class PCBRender2 extends React.Component {
  loading_color = '#555888'

  constructor(props) {
    super(props)
    this.state = {
      img: '',
    }
  }

  async componentDidMount() {
    const fw = this.props.store.get('frameworks')
    const data = await fw.PCBApi.render_svg({
      project_key: this.props.project_key,
      username: this.props.username,
      side: this.props.side,
    })
    this.setState({img: 'data:image/svg+xml;base64,' + data})
  }

  render() {
    let { classes } = this.props

    return (!this.state.img.length)
      ? <div className={classes.loadingDiv}><ReactLoading type={'spinningBubbles'} color={this.loading_color} height={50} width={50} /></div>
      : <img src={this.state.img}/>
  }
}

class ProjectRender extends React.Component {

  render() {
    const { project, classes } = this.props

    return <div>
      <table border="0" cellSpacing="2">
        <tbody>
          <tr>
            <td>
              <PCBRender store={this.props.store} project_key={project.project_key} username={project.username} side='top'/>
            </td>
            <td>
              <PCBRender store={this.props.store} project_key={project.project_key} username={project.username} side='bottom'/>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  }
}

class ProjectCAM extends React.Component {
  render() {
    const {project, classes} = this.props
    return <div>
      {
        project.is_ours ? <material.Button onClick={this.handleDownloadCAM}>Generate CAM</material.Button> : <div></div>
      }
      {/*<table border="0" cellSpacing="2">*/}
        {/*<tbody>*/}
        {/*<tr>*/}
          {/*<td>*/}
            {/*<PCBRender2 store={this.props.store} project_key={project.project_key} username={project.username}*/}
                        {/*side='top'/>*/}
          {/*</td>*/}
          {/*<td>*/}
            {/*<PCBRender2 store={this.props.store} project_key={project.project_key} username={project.username}*/}
                        {/*side='bottom'/>*/}
          {/*</td>*/}
        {/*</tr>*/}
        {/*</tbody>*/}
      {/*</table>*/}
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
        {
          project.files.map(f => {
            return <tr key={f.project_file_id}>
              <td colSpan={3}>{f.file_name}</td>
              <td colSpan={1}>{moment.duration(f.uploaded_ago, 'seconds').humanize()}</td>
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
      tabValue: 0,
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

  handleTabChange = (event, tabValue) => {
    this.setState({ tabValue })
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
            <ProjectDetails project={project}/>
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
          <material.Button onClick={this.handleUpload}>Upload</material.Button>
        </material.DialogContent>
      </material.Dialog>

    </material.Paper>
  }
}

PCBRender = withStore(withStyles(pcbrenderStyle)(PCBRender))
// PCBRender2 = withStore(withStyles(renderStyle)(PCBRender2))
ProjectDetails = withStore(withStyles(detailsStyle)(ProjectDetails))
ProjectRender = withStore(withStyles(renderStyle)(ProjectRender))
ProjectCAM = withStore(withStyles(camStyle)(ProjectCAM))

export default withStore(withStyles(style)(Project))

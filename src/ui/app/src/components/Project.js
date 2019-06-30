import React from 'react'
import ReactLoading from 'react-loading';

import * as material from '@material-ui/core'

import { withStyles } from '@material-ui/core/styles'
import { withRouter } from 'react-router'

import { withStore } from '../global-store'
import DropzoneArea from './dropzone/DropZoneArea'

import { Status } from '../framework_client'


const renderStyle = theme => ({
  'loadingDiv': {
    height: '600px',
    width: '600px',
    display: 'flex',
    'align-items': 'center',
    'justify-content': 'center',
  },

  'loading': {
  }
})


const style = theme => ({
})



class PCBRender extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      img: '',
      width: 600,
      height: 600,
      loading_color: '#555888'
    };
  };

  componentDidMount() {
    this.updateImage()
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    if (prevProps === this.props) return

    console.log('update', this.props)
    this.updateImage()
  }

  updateImage() {
    if (this.props.project_key === null) {
      return
    }

    let fw = this.props.store.get('frameworks')
    fw.PCBApi.render({
      project_key: this.props.project_key,
      username: this.props.username,
      side: this.props.side,

    }).then(
      data => this.setState({img: 'data:image/jpeg;base64,' + data})
    )

  }

  render() {
    let { classes } = this.props
    let loading =  (this.props.project_key === null || !this.state.img.length)

    return (loading)
      ? <div className={classes.loadingDiv}><ReactLoading className={classes.loading} type={'spinningBubbles'} color={this.state.loading_color} height={50} width={50} /></div>
      : <img src={this.state.img}/>
  }
}


class Project extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      uploadModal: false,
      files: [],
      project_key: null,
      project: null,
      username: null,
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
    let username = this.props.match.params.username
    let project_key = this.props.match.params.project_key

    let { store } = this.props
    let fw = store.get('frameworks')
    fw.ProjectsApi.project({project_key: project_key, username: username}).then(data => {
      console.log("data", project_key, username, data)
      this.setState({
        ...this.state,
        project_key: project_key,
        username: username,
        project: data,
      })
    })
  }

  render() {
    const { classes } = this.props
    const { project } = this.state
    console.log('render', this.state, this.props)

    if (project === null) {
      return <div>Loading</div>
    }

    console.log('status', project.status)

    if (project.status === 404) {
      return <div>{project.details}</div>
    } else if (project instanceof Status) {
      return <div>Error: project.details</div>
    }

    return <material.Paper className={classes.paper}>
      <table border="0" cellspacing="2">
        <tbody>
        <tr>
            <td colSpan="2">
            {
              project.is_ours ? <material.Button onClick={this.handleOpen}>Upload Gerber File(s)</material.Button> : <div></div>
            }

            </td>
          </tr>
          <tr>
            <td>
              <PCBRender project_key={this.state.project_key} username={this.state.username} side='top'/>
            </td>
            <td>
              <PCBRender project_key={this.state.project_key} username={this.state.username} side='bottom'/>
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

PCBRender = withStore(withStyles(renderStyle)(PCBRender))

export default withRouter(withStore(withStyles(style)(Project)))
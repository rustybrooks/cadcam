import React from 'react'
import ReactLoading from 'react-loading'
import * as material from '@material-ui/core'

import { withStyles } from '@material-ui/core/styles'
import { withStore } from '../../global-store'

import Gcode from './Gcode'

const style = theme => ({
  'loadingDiv': {
    height: '600px',
    width: '600px',
    display: 'flex',
    'align-items': 'center',
    'justify-content': 'center',
  },
  'forms': {
    'align-items': 'top'
  },
  'root': {},
  'image': {
    'align-items': 'top',
    // background: 'green',
    display: 'flex',
  }
})

class CAMRender extends React.Component {
  loading_color = '#555888'

  constructor(props) {
    super(props)
    this.state = {
      show_image: true,
      img: '',
      cam: null
    }
  }

  componentDidMount() {
    this.updateImage()
  }

  componentDidUpdate(prevProps, prevState) {
    if (this.props.regenerate === prevProps.regenerate && this.props.regenerate_download === prevProps.regenerate_download) return
    this.updateImage(this.props.regenerate_download !== prevProps.regenerate_download)
  }

  async updateImage(download=false) {
    const { params } = this.props
    const fw = this.props.store.get('frameworks')
    this.setState({img: ''})
    const args = {
      download: download,
      url_token: localStorage.getItem('api-key'),
      project_key: this.props.project_key,
      username: this.props.username,
      side: this.props.side,
      depth: params.cut_depth,
      separation: params.trace_separation,
      border: params.border,
      thickness: params.thickness,
      panelx: params.panelx,
      panely: params.panely,
      zprobe_type: params.zprobe_type,
      posts: params.posts,
      max_width: 700,
      max_height: 700,
    }
    // console.log(args)
    const data = await fw.PCBApi.render_cam(args)
    this.setState({...this.state, img: 'data:image/svg+xml;base64,' + data.image, cam: data.cam})
  }

  swapImage = () => {
    this.setState({...this.state, show_image: !this.state.show_image})
  }

  render() {
    const { classes } = this.props

    // console.log("rendercam props", this.props)

    return (
      <div className={classes.root}>
        <div>
          <material.Button onClick={this.swapImage}>Swap to {this.state.show_image ? "CAM" : "Image"}</material.Button>
        </div>
        <div className={classes.image}>
        {
          (!this.state.img.length)
            ? <div className={classes.loadingDiv}><ReactLoading type={'spinningBubbles'} color={this.loading_color} height={75} width={75} /></div>
            : (this.state.show_image ? <img src={this.state.img}/> : <Gcode cam={this.state.cam}></Gcode>)
        }
        </div>
      </div>
    )
  }
}

export default withStore(withStyles(style)(CAMRender))

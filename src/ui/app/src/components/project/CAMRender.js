import React from 'react'
import ReactLoading from 'react-loading'

import { withStyles } from '@material-ui/core/styles'
import { withStore } from '../../global-store'


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
  'root': {
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
      img: '',
    }
  }

  componentDidMount() {
    this.updateImage()
  }

  componentDidUpdate(prevProps, prevState) {
    if (this.props.regenerate === prevProps.regenerate) return
    this.updateImage()
  }

  async updateImage() {
    const { params } = this.props
    const fw = this.props.store.get('frameworks')
    this.setState({img: ''})
    const args = {
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
      max_width: 800,
      max_height: 800,
    }
    console.log(args)
    const data = await fw.PCBApi.render_cam(args)
    this.setState({img: 'data:image/svg+xml;base64,' + data})
  }

  render() {
    const { classes } = this.props

    // console.log("rendercam props", this.props)

    return (
      <div className={classes.root}>
        {
          (!this.state.img.length)
            ? <div className={classes.loadingDiv}><ReactLoading type={'spinningBubbles'} color={this.loading_color} height={75} width={75} /></div>
            : <img src={this.state.img}/>
        }
      </div>
    )
  }
}

export default withStore(withStyles(style)(CAMRender))

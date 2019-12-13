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
    if (this.state.layers === prevState.layers) return
    this.updateImage()
  }

  async updateImage() {
    const fw = this.props.store.get('frameworks')
    this.setState({img: ''})
    const args = {
      project_key: this.props.project_key,
      username: this.props.username,
      side: this.props.side,
      depth: 0.005,
      separation: 0.020,
      border: 0,
      thickness: 1.7,
      panelx: 1,
      panely: 1,
      zprobe_type: this.props.zprobe_type,
      posts: null,
      max_width: 600,
      max_height: 600,
    }
    console.log(args)
    const data = await fw.PCBApi.render_cam(args)
    this.setState({img: 'data:image/svg+xml;base64,' + data})
  }

  render() {
    const { classes } = this.props

    console.log("rendercam props", this.props)

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

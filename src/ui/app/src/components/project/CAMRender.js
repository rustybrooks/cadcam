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
    }
  }

  swapImage = () => {
    this.setState({...this.state, show_image: !this.state.show_image})
  }

  render() {
    const { classes, img, cam } = this.props

    console.log('cam render')
    if (!img) {
      return <div>Nuttin</div>
    }
    console.log("not nuttin", img)

    return (
      <div className={classes.root}>
        <div>
          <material.Button onClick={this.swapImage}>Swap to {this.state.show_image ? "Gcode" : "Image"}</material.Button>
        </div>
        <div className={classes.image}>
        {
          (img === 'running')
            ? <div className={classes.loadingDiv}><ReactLoading type={'spinningBubbles'} color={this.loading_color} height={75} width={75} /></div>
            : (this.state.show_image ? <img src={'data:image/svg+xml;base64,' + img}/> : <Gcode cam={cam}/>)
        }
        </div>
      </div>
    )
  }
}

export default withStore(withStyles(style)(CAMRender))

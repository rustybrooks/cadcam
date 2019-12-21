import React from 'react'
import ReactLoading from 'react-loading'
import * as m from '@material-ui/core'

import { withStyles } from '@material-ui/core/styles'
import { withStore } from '../../global-store'

import Gcode from './Gcode'

import { BASE_URL } from '../../constants/api'


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
  },
  'message': {
    'padding': '10px',
    'height': '200px',
    'align-items': 'center',
    'margin': theme.spacing(1)
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

    if (!img) {
      return <m.Typography className={classes.message}>Set parameters and click 'generate' to see results</m.Typography>
    }

    const url = BASE_URL + '/api/projects/download_file/' + img.file_name + '?project_file_id=' + img.project_file_id


    return (
      <div className={classes.root}>
        <div>
          <m.Button onClick={this.swapImage}>Swap to {this.state.show_image ? "Gcode" : "Image"}</m.Button>
        </div>
        <div className={classes.image}>
        {
          (img === 'running')
            ? <div className={classes.loadingDiv}><ReactLoading type={'spinningBubbles'} color={this.loading_color} height={75} width={75} /></div>
            : (this.state.show_image ? <img src={url} /> : <Gcode cam={cam}/>)
        }
        </div>
      </div>
    )
  }
}

export default withStore(withStyles(style)(CAMRender))

import React from 'react'
import ReactLoading from 'react-loading'
import * as material from '@material-ui/core'

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


class PCBRender extends React.Component {
  loading_color = '#555888'

  constructor(props) {
    super(props)
    this.state = {
      img: '',
      layers: {
        copper: true,
        'solder-mask': true,
        'silk-screen': true,
        drill: true,
      }
    }

    // This binding is necessary to make `this` work in the callback
    this.handleChange = this.handleChange.bind(this)
  }

  handleChange = name => event => {
    this.setState({layers: {...this.state.layers, [name]: event.target.checked }})
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
    const solderMask = this.state.layers['solder-mask']
    const silkScreen = this.state.layers['silk-screen']

    return (
      <div className={classes.root}>
        <div className={classes.forms}>
          <material.FormGroup row>
            <material.FormControlLabel
              control={<material.Checkbox checked={copper} onChange={this.handleChange('copper')} value="copper" />}
              label="Copper"
            />
            <material.FormControlLabel
              control={<material.Checkbox checked={solderMask} onChange={this.handleChange('solder-mask')} value="solder-mask" />}
              label="Solder Mask"
            />
            <material.FormControlLabel
              control={<material.Checkbox checked={silkScreen} onChange={this.handleChange('silk-screen')} value="silk-screen" />}
              label="Silk Screen"
            />
            <material.FormControlLabel
              control={<material.Checkbox checked={drill} onChange={this.handleChange('drill')} value="drill" />}
              label="Drill"
            />
          </material.FormGroup>
          {
            (!this.state.img.length)
              ? <div className={classes.loadingDiv}><ReactLoading type={'spinningBubbles'} color={this.loading_color} height={75} width={75} /></div>
              : <img src={this.state.img}/>
          }
        </div>
      </div>
    )
  }
}

export default withStore(withStyles(style)(PCBRender))

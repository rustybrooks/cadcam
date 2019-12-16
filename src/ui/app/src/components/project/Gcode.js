import React from 'react'
import * as material from '@material-ui/core'

import { withRouter } from 'react-router'
import { withStore } from '../../global-store'
import { withStyles } from '@material-ui/core/styles'


const style = theme => ({
  root: {
    display: 'flex',
  },
  'files': {
    flex: '0 0 25%',
    backgroundColor: theme.palette.background.paper,
  },
  'code': {
    flex: 1,
  }
})


class Gcode extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      selected: Object.keys(props.cam)[0]
    }

    this.handleListItemClick = this.handleListItemClick.bind(this)
  }

  handleListItemClick = (event, index) => {
    this.setState({...this.state, selected: index})
  };

  render() {
    const { store, classes, cam } = this.props
    return <div className={classes.root}>
      <material.List className={classes.files}>
        {
          Object.keys(cam).map((x) => {
            return <material.ListItem
              key={x}
              button selected={this.state.selected === x}
              onClick={event => this.handleListItemClick(event, x)}
            >{x}</material.ListItem>
          })
        }

      </material.List>
      <material.Paper className={classes.code}>
        <pre className={classes.code}>
          {/*{this.state.selected ? this.props.cam[this.state.selected].split ('\n').map ((item, i) => <span key={i}>{item}<br/></span>) : ''}*/}
          {this.state.selected ? this.props.cam[this.state.selected] : ''}
        </pre>
      </material.Paper>
    </div>
  }

}

export default withRouter(withStore(withStyles(style)(Gcode)))


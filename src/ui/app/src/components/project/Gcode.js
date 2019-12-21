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
      selected: props.cam[0].file_name,
      data: '',
    }

    this.handleListItemClick = this.handleListItemClick.bind(this)
    this.updateText(props.cam[0].project_file_id)
  }

  handleListItemClick = (event, index) => {
    this.setState({...this.state, selected: this.props.cam[index].project_file_id})
    this.updateText(this.props.cam[index].project_file_id)
  };

  async updateText(project_file_id) {
    const fw = this.props.store.get('frameworks')
    const data = await fw.ProjectsApi.download_file({file_name: null, project_file_id: project_file_id, as_json: true})
    this.setState({...this.state, data: data.content})
  }

  render() {
    const { store, classes, cam } = this.props
    return <div className={classes.root}>
      <material.List className={classes.files}>
        {
          cam.map((x, i) => {
            return <material.ListItem
              key={x.file_name}
              button selected={this.state.selected === x.file_name}
              onClick={event => this.handleListItemClick(event, i)}
            >{x.file_name}</material.ListItem>
          })
        }

      </material.List>
      <material.Paper className={classes.code}>
        <pre className={classes.code}>
          {/*{this.state.selected ? this.props.cam[this.state.selected].split ('\n').map ((item, i) => <span key={i}>{item}<br/></span>) : ''}*/}
          {this.state.data}
        </pre>
      </material.Paper>
    </div>
  }

}

export default withRouter(withStore(withStyles(style)(Gcode)))


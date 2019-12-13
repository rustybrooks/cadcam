import React from 'react'
import * as material from '@material-ui/core'

import { withStyles } from '@material-ui/core/styles'


import { withStore } from '../../global-store'


import CAMRender from './CAMRender'

const style = theme => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 120,
  },
})


class ProjectCAM extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      regenerate: 0,
      params: {
        'cut_depth': [0.005, 'in'],
        'trace_separation': [0.015, 'in'],
        'zprobe_type': 'none',
        'border': [0, 'in'],
        'thickness': [.067, 'in'],
        'panelx': 1,
        'panely': 1,
        'posts': 'none',
        'two_sided': false,
      }
    }
  }

  handleGenerate = event => {
    this.setState({...this.state, regenerate: this.state.regenerate+1})
  }

  handleChange = name => event => {
    console.log("Set", name, event.target.value)
    this.setState({
      ...this.state,
      params: {
        ...this.state.params,
        [name]: event.target.value,
      }
    });
  };

  render() {
    const { classes, project } = this.props

    return <div className={classes.root}>
      <div className={classes.forms}>
        <material.FormGroup row>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="zprobe-type-label">Z Probe Type</material.InputLabel>
            <material.Select
              labelId="trace_depth-label" id="zprobe-type-select"
              value={this.state.params.zprobe_type} onChange={this.handleChange('zprobe_type').bind(this)}
            >
              <material.MenuItem value='none'>None</material.MenuItem>
              <material.MenuItem value='auto'>Auto</material.MenuItem>
            </material.Select>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="trace-depth-label">Cut depth</material.InputLabel>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="trace-depth-label">Trace separation</material.InputLabel>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="border-label">Border</material.InputLabel>
          </material.FormControl>


          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="panel-x-label">Z Probe Type</material.InputLabel>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="panel-y-label">Cut depth</material.InputLabel>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="two-sided-label">Two sided</material.InputLabel>
          </material.FormControl>

        </material.FormGroup>
      </div>

      <material.Button color="primary" variant="outlined" onClick={this.handleGenerate.bind(this)}>Generate</material.Button>

      <table border={0} cellSpacing={2}>
        <tbody>
          <tr>
            <td valign="top">
              <CAMRender
                store={this.props.store} project_key={project.project_key} username={project.username} side='top'
                params={this.state.params} regenerate={this.state.regenerate}
              />
            </td>
            <td valign="top">
              <CAMRender store={this.props.store} project_key={project.project_key} username={project.username} side='bottom'
                         params={this.state.params} regenerate={this.state.regenerate}
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  }
}

export default withStore(withStyles(style)(ProjectCAM))

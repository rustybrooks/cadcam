import React from 'react'
import * as material from '@material-ui/core'

import { withStyles } from '@material-ui/core/styles'


import { withStore } from '../../global-store'


import CAMRender from './CAMRender'

const style = theme => ({
  root: {
    '& .MuiTextField-root': {
      margin: theme.spacing(1),
      width: 200,
    },
  },

  formControl: {
    margin: theme.spacing(1),
    minWidth: 120,
  },

  render: {
    width: '50%'
  }
})


class ProjectCAM extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      regenerate: 0,
      params: {
        'cut_depth': 0.007,
        'trace_separation': 0.017,
        'zprobe_type': 'none',
        'border': 0,
        'thickness': .067,
        'panelx': 1,
        'panely': 1,
        'posts': 'none',
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

    return <div className={classes.forms}>
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
            <material.TextField
              id="trace-depth-entry" label="Cut Depth"
              value={this.state.params.cut_depth} onChange={this.handleChange('cut_depth').bind(this)}
              type="number"
              inputProps={{ min: "0.001", max: "0.100", step: "0.001" }}
            />
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.TextField
              id="trace-separation-entry" label="Trace separation"
              value={this.state.params.trace_separation}
              onChange={this.handleChange('trace_separation').bind(this)}
              type="number"
              inputProps={{ min: "0.001", max: "0.100", step: "0.001" }}
            />
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.TextField
              id="border-entry" label="Border" value={this.state.params.border}
              type="number"
              inputProps={{ min: "0.0", max: "1.0", step: "0.1" }}
            />
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.TextField
              id="panel-x-entry" label="Panel X" value={this.state.params.panelx}
              type="number"
              onChange={this.handleChange('panelx').bind(this)}
              inputProps={{ min: "1", max: "10", step: "1" }}
            />
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.TextField
              id="panel-y-entry" label="Panel Y" value={this.state.params.panely}
              type="number"
              onChange={this.handleChange('panely').bind(this)}
              inputProps={{ min: "1", max: "10", step: "1" }}
            />
          </material.FormControl>


        </material.FormGroup>

      <material.Button color="primary" variant="outlined" onClick={this.handleGenerate.bind(this)}>Generate</material.Button>
      {
        // project.is_ours ? <material.Button color="primary" variant="outlined" onClick={this.handleGenerateDownload.bind(this)}>Generate and Save</material.Button> : <div></div>
      }

      <table border={0} cellSpacing={2}>
        <tbody>
          <tr>
            <td valign="top" width="50%">
              <CAMRender
                className={classes.render}  project_key={project.project_key} username={project.username} side='top'
                params={this.state.params} regenerate={this.state.regenerate}
              />
            </td>
            <td valign="top" width="50%">
              <CAMRender className={classes.render} project_key={project.project_key} username={project.username} side='bottom'
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

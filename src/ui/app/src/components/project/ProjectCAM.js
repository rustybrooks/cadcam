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
      error: null,
      top: {
        img: null,
        cam: [],
      },
      bottom: {
        img: null,
        cam: [],
      },
      params: {
        'depth': 0.007,
        'separation': 0.017,
        'zprobe_type': 'none',
        'border': 0,
        'thickness': .067,
        'panelx': 1,
        'panely': 1,
        'posts': 'none',
        'drill': 'top',
        'cutout': 'top',
        'iso_bit': 'engrave-0.1mm-30deg',
        'drill_bit': 'straight-1.0mm',
        'cutout_bit': 'straight-3.0mm',
        'post_bit': 'straight-3.0mm',
      }
    }
  }

  handleChange = name => event => {
    this.setState({
      ...this.state,
      params: {
        ...this.state.params,
        [name]: event.target.value,
      }
    });
  };

  async updateImage(download=false) {
    this.setState({
      ...this.state,
      'error': null,
      'top': {'img': 'running'},
      'bottom': {'img': 'running'},
    })

    const { params } = this.state
    const { project, store } = this.props
    const fw = store.get('frameworks')
    const args = {
      download: false,
      project_key: project.project_key,
      username: project.username,
      side: 'both',
      max_width: 600,
      max_height: 600,
    }
    Object.assign(args, params)
    const tools = store.get('tools')
    const vars = ['iso_bit', 'drill_bit', 'cutout_bit', 'post_bit']
    vars.forEach(v => {
      const found = tools.find(f => {
        return f.tool_key === args[v]
      })
      args[v] = {tool_key: found.tool_key, user_id: found.user_id}
    })
    const data = await fw.PCBApi.render_cam(args)

    if (data.hasOwnProperty('status') && data.hasOwnProperty('details')) {
      this.setState({
        ...this.state, error: data.details,
        'top': {'img': null},
        'bottom': {'img': null},
      })
    } else {
      let top_img_file = null
      let bot_img_file = null
      let top_cam_files = []
      let bot_cam_files = []
      data.files.forEach(f => {
        if (f.file_name === 'top_cam.svg') {
          top_img_file = f
        } else if (f.file_name === 'bottom_cam.svg') {
          bot_img_file = f
        } else if (f.file_name.startsWith('pcb_top')) {
          top_cam_files.push(f)
        } else if (f.file_name.startsWith('pcb_bot')) {
          bot_cam_files.push(f)
        }
      })

      console.log(top_img_file, bot_img_file, top_cam_files, bot_cam_files)

      this.setState({
        ...this.state,
        'error': null,
        'top': {'img': top_img_file, 'cam': top_cam_files},
        'bottom': {'img': bot_img_file, 'cam': bot_cam_files},
      })
    }
  }

  render() {
    const { classes, project, store } = this.props

    const tools = store.get('tools')
    const drill_tools = tools.filter(x => x.type === 'straight')

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
            <material.InputLabel id="iso-bit-label">Isolation tool</material.InputLabel>
            <material.Select
              labelId="iso-bit-label" id="iso-bit-select"
              value={this.state.params.iso_bit} onChange={this.handleChange('iso_bit').bind(this)}
            >
              {tools.map(x => <material.MenuItem key={x.tool_id} value={x.tool_key}>{x.tool_key}</material.MenuItem>)}
            </material.Select>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="drill-bit-label">Drill tool</material.InputLabel>
            <material.Select
              labelId="drill-bit-label" id="drill-bit-select"
              value={this.state.params.drill_bit} onChange={this.handleChange('drill_bit').bind(this)}
            >
              {drill_tools.map(x => <material.MenuItem key={x.tool_id} value={x.tool_key}>{x.tool_key}</material.MenuItem>)}
            </material.Select>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="cutout-bit-label">Cutout tool</material.InputLabel>
            <material.Select
              labelId="cutout-bit-label" id="cutout-bit-select"
              value={this.state.params.cutout_bit} onChange={this.handleChange('cutout_bit').bind(this)}
            >
              {drill_tools.map(x => <material.MenuItem key={x.tool_id} value={x.tool_key}>{x.tool_key}</material.MenuItem>)}
            </material.Select>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.InputLabel id="post-bit-label">Post tool</material.InputLabel>
            <material.Select
              labelId="post-bit-label" id="post-bit-select"
              value={this.state.params.post_bit} onChange={this.handleChange('post_bit').bind(this)}
            >
              {drill_tools.map(x => <material.MenuItem key={x.tool_id} value={x.tool_key}>{x.tool_key}</material.MenuItem>)}
            </material.Select>
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.TextField
              id="trace-depth-entry" label="Cut Depth"
              value={this.state.params.depth} onChange={this.handleChange('depth').bind(this)}
              type="number"
              inputProps={{ min: "0.001", max: "0.100", step: "0.001" }}
            />
          </material.FormControl>

          <material.FormControl className={classes.formControl}>
            <material.TextField
              id="trace-separation-entry" label="Trace separation"
              value={this.state.params.separation}
              onChange={this.handleChange('separation').bind(this)}
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

          <material.FormControl component="fieldset">
              <material.FormLabel component="legend">Drill Side</material.FormLabel>
              <material.RadioGroup aria-label="position" name="position" value={this.state.params.drill} onChange={this.handleChange('drill').bind(this)} row>
                <material.FormControlLabel
                  value="top"
                  control={<material.Radio color="primary" />}
                  label="top"
                  labelPlacement="end"
                />
                <material.FormControlLabel
                  value="bottom"
                  control={<material.Radio color="primary" />}
                  label="bottom"
                  labelPlacement="end"
                />

              </material.RadioGroup>
            </material.FormControl>

          <material.FormControl component="fieldset">
              <material.FormLabel component="legend">Cutout Side</material.FormLabel>
              <material.RadioGroup aria-label="position" name="position" value={this.state.params.cutout} onChange={this.handleChange('cutout').bind(this)} row>
                <material.FormControlLabel
                  value="top"
                  control={<material.Radio color="primary" />}
                  label="top"
                  labelPlacement="end"
                />
                <material.FormControlLabel
                  value="bottom"
                  control={<material.Radio color="primary" />}
                  label="bottom"
                  labelPlacement="end"
                />

              </material.RadioGroup>
            </material.FormControl>

        </material.FormGroup>

      <material.Button color="primary" variant="outlined" onClick={this.updateImage.bind(this)}>Generate</material.Button>
      {
        this.state.error ? <material.Typography color='error'>{this.state.error}</material.Typography> : ''
      }


      <table border={0} cellSpacing={2}>
        <tbody>
          <tr>
            <td valign="top" width="50%">
              <CAMRender
                className={classes.render} img={this.state.top.img} cam={this.state.top.cam} />
            </td>
            <td valign="top" width="50%">
              <CAMRender className={classes.render} img={this.state.bottom.img} cam={this.state.bottom.cam} />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  }
}

export default withStore(withStyles(style)(ProjectCAM), ['tools'])

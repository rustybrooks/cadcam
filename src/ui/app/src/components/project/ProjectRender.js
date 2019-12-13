import React from 'react'
import { withStyles } from '@material-ui/core/styles'
import { withStore } from '../../global-store'

import PCBRender from './PCBRender'

const style = theme => ({
  forms: {
  },
  formControl: {
    margin: theme.spacing(1),
    minWidth: 120,
  },
})


class ProjectRender extends React.Component {
  render() {
    const { project, classes } = this.props

    return <div>
      <table border="0" cellSpacing="2">
        <tbody>
          <tr>
            <td valign="top">
              <PCBRender store={this.props.store} project_key={project.project_key} username={project.username} side='top'/>
            </td>
            <td valign="top">
              <PCBRender store={this.props.store} project_key={project.project_key} username={project.username} side='bottom'/>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  }
}

export default withStore(withStyles(style)(ProjectRender))
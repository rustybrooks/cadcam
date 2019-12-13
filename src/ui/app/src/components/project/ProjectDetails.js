import React from 'react'
import * as material from '@material-ui/core'
import * as moment from 'moment'

import { withStyles } from '@material-ui/core/styles'


import { withStore } from '../../global-store'

const style = theme => ({
})


class ProjectDetails extends React.Component {
  render () {
    const { project, classes } = this.props

    return <div>
      <table border={1} cellSpacing={0} cellPadding={5}>
        <tbody>
        <tr>
          <th align="left">Project Key</th><td colSpan={3}>{project.project_key}</td>
        </tr>

        <tr>
          <th align="left">Project Name</th><td colSpan={3}>{project.name}</td>
        </tr>

        <tr>
          <th align="left">Owner</th><td colSpan={3}>{project.username}</td>
        </tr>

        <tr>
          <th align="left">Created</th><td>{moment.duration(project.created_ago, 'seconds').humanize()}</td>
          <th align="left">Updated</th><td>{moment.duration(project.modified_ago, 'seconds').humanize()}</td>
        </tr>

        <tr>
          <th colSpan={4} align="left">
            Files
          </th>
        </tr>
        <tr>
          <td colSpan={4}>
          <material.Button variant='outlined' onClick={this.props.handleOpen} color="primary">
            Add Files
          </material.Button>
          </td>
        </tr>
        {
          project.files.map(f => {
            return <tr key={f.project_file_id}>
              <td colSpan={3}>{f.file_name}</td>
              <td colSpan={1}>{moment.duration(f.uploaded_ago, 'seconds').humanize()}</td>
              <td>
                <material.Button onClick={() => {window.location.href = 'http://localhost:5000/api/projects/download_file/' + project.project_key + '-' + f.file_name + '?project_file_id=' + f.project_file_id; return null;}} variant='outlined' color="primary">
                  Download
                </material.Button>
              </td>
            </tr>
          })
        }
        </tbody>
      </table>
    </div>
  }
}

export default withStore(withStyles(style)(ProjectDetails))
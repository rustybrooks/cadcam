import React from 'react'
import * as material from '@material-ui/core'
import * as moment from 'moment'

import { withStyles } from '@material-ui/core/styles'


import { withStore } from '../../global-store'

import { BASE_URL } from '../../constants/api'


const style = theme => ({
})


class ProjectDetails extends React.Component {
  constructor(props) {
    super(props)

    // This binding is necessary to make `this` work in the callback
    this.handleDelete = this.handleDelete.bind(this)
  }


  handleDelete = (project_file_id) => () => {
    const { store } = this.props
    const fw = store.get('frameworks')

    fw.ProjectsApi.delete_file({project_key: this.props.project.project_key, project_file_id: project_file_id}).then(data => console.log(data))
    this.props.update()
  }

  downloadFile = (file_name, project_file_id) => async () => {
    const { store } = this.props
    const fw = store.get('frameworks')

    const data = await fw.UserApi.generate_temp_token({})
    console.log('data =', data)
    const { project } = this.props
    const url = BASE_URL + '/api/projects/download_file/' + project.project_key + '-' + file_name + '?project_file_id=' + project_file_id + '&url_token=' + data
    console.log(url)
    window.location.href = url
  }

  render () {
    const { project, classes, store } = this.props

    const user = store.get('user')

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
            {!user ? '' : (
              <material.Button variant='outlined' onClick={this.props.handleOpen} color="primary">
                Add Files
              </material.Button>
            )
            }
          </td>
        </tr>
        {
          project.files.map(f => {
            return <tr key={f.project_file_id}>
              <td colSpan={3}>{f.file_name}</td>
              <td colSpan={1}>{moment.duration(f.uploaded_ago, 'seconds').humanize()}</td>
              <td>
                <material.Button onClick={this.downloadFile(f.file_name, f.project_file_id).bind(this)} variant='outlined' color="primary">
                  Download
                </material.Button>
                {
                  project.is_ours ? <material.Button onClick={this.handleDelete(f.project_file_id)}>Delete</material.Button> : <div></div>
                }

              </td>
            </tr>
          })
        }
        </tbody>
      </table>
    </div>
  }
}

export default withStore(withStyles(style)(ProjectDetails), ['user'])

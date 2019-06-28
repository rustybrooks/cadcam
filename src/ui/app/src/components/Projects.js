import React from 'react'
import Paper from '@material-ui/core/Paper'
import { withStyles } from '@material-ui/core/styles'
import { withStore } from '../global-store'

const style = theme => ({
  'paper': {

  }
});


class Projects extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
    };
  }

  componentDidMount() {
      this.updateProjects()
  }

  updateProjects() {
    const { store } = this.props
    let fw = store.get('frameworks')
    if (fw === null || fw === undefined) return

    store.set('projects', null)
    fw.ProjectsApi.index().then(data => store.set('projects', data))
  }

  render() {
    const { store, classes } = this.props

    if (store.get('projects') === undefined) {
      return <div>...</div>
    } else if (store.get('projects') === null) {
      return <div>Loading...</div>
    }

    return (
      <Paper className={classes.paper}>Projects</Paper>
    )
  }
}

export default withStore(withStyles(style)(Projects))
import React from 'react'
import { Link } from 'react-router-dom'
import Paper from '@material-ui/core/Paper'
import Button from '@material-ui/core/Button'
import TablePagination from '@material-ui/core/TablePagination'
import { withStyles } from '@material-ui/core/styles'
import TextField from '@material-ui/core/TextField';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';

import { withRouter } from 'react-router'

import { withStore } from '../global-store'
import CreateProject from './CreateProject'

const style = theme => ({
  root: {
    // width: '100%',
    // maxWidth: 1010,
    marginTop: theme.spacing(1),
    // backgroundColor: 'green',
  },
})


function getSorting(order, orderBy) {
  return order === 'desc'
    ? (a, b) => (b[orderBy] < a[orderBy] ? -1 : 1)
    : (a, b) => (a[orderBy] < b[orderBy] ? -1 : 1);
}


class ProjectRow extends React.Component {

  render() {
    let x = this.props.row
    const {classes} = this.props;
    return <tr key={1} className={this.props.selected ?
      (this.props.even ? classes.matchrow_select_even : classes.matchrow_select_odd) :
      (this.props.even ? classes.matchrow_even : classes.matchrow_odd)
    }>
      <td className={classes.matchlist}>
        <Typography gutterBottom>
          {x.map_name === 'Erangel_Main' ? 'Erangel' : (x.map_name === 'Desert_Main' ? 'Miramar' : (x.map_name === 'Savage_Main' ? 'Sanhok' : 'Vikendi'))}
        </Typography>
        <Typography gutterBottom>{x.game_mode}</Typography>
        <Typography color="textSecondary">{sprintf("%2d / %2dm", x.timesurvived / 60, x.duration / 60)}</Typography>
      </td>
    </tr>
  }
}

class Projects extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      order: 'desc',
      orderBy: 'created_at',
      page: 0,
      rowsPerPage: 10,
      showMatch: null,
      createModal: false,
    };

    // This binding is necessary to make `this` work in the callback
    this.handleClose = this.handleClose.bind(this);
    // this.handleCreate = this.handleCreate.bind(this);
  }

  componentDidUpdate(prevProps) {
    if (this.props.location.pathname !== prevProps.location.pathname) {
      this.setTimer()
      this.onRouteChanged()
    }

    //if (this.props.league && !prevProps.league) {
    //  this.onRouteChanged()
   // }
  }

  componentDidMount() {
    this.updateProjects()
    this.onRouteChanged()
  }

  onRouteChanged() {
    console.log('route', this.props.location.pathname)
    if (this.props.location.pathname === '/projects/create') {
      this.setState({...this.state, createModal: true})
    }
  }

  updateProjects() {
    const { store } = this.props
    let fw = store.get('frameworks')
    if (fw === null || fw === undefined) return

    store.set('projects', null)
    fw.ProjectsApi.index({page: 1, limit: 100}).then(data => store.set('projects', data))
  }

  handleRequestSort = (event, property) => {
    const orderBy = property;
    let order = 'desc';

    if (this.state.orderBy === property && this.state.order === 'desc') {
      order = 'asc';
    }

    this.setState({ order, orderBy });
  };

  handleChangePage = (event, page) => {
    this.setState({ page });
  };

  handleChangeRowsPerPage = event => {
    this.setState({ rowsPerPage: event.target.value });
  };

  handleClose() {
    // this.setState({...this.state, 'createModal': false})
    // console.log("closing")
      this.props.history.push('/projects')

  }


  render() {
    const { store, classes } = this.props

    let projects = store.get('projects')
    if (projects === undefined) {
      return <div>...</div>
    } else if (projects === null) {
      return <div>Loading...</div>
    }

    console.log("projects", projects)

    let even = true
    let owner = this
    const { order, orderBy, selected, rowsPerPage, page } = this.state;

    return (
      <Paper className={classes.paper}>
        <Button component={Link} to="/projects/create">Create New Project</Button>

        <div className={classes.root}>
          <TablePagination
            style={{maxWidth: 600}}
            component="div"
            count={projects.results.length}
            rowsPerPage={rowsPerPage}
            rowsPerPageOptions={[10, 25, 50, 100]}
            page={page}
            backIconButtonProps={{
              'aria-label': 'Previous Page',
            }}
            nextIconButtonProps={{
              'aria-label': 'Next Page',
            }}
            onChangePage={this.handleChangePage}
            onChangeRowsPerPage={this.handleChangeRowsPerPage}
          />

          <table className={classes.matchtable}>
            <tbody>

            {projects['results'].sort(getSorting(order, orderBy))
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map(x => {
                even = !even
                return (
                  <ProjectRow
                    //classes={classes} key={x.match_id} playerName={this.props.playerName} row={x}
                    //onClick={() => that.setState({showMatch: this.state.showMatch === x.match_id ? null : x.match_id})}
                    //even={even} buttonLabel={(this.state.showMatch === x.match_id) ? "Less" : "More"}
                    //fullsize={!this.state.showMatch} selected={x.match_id === this.state.showMatch}
                    // component={Link} to={"/player/" + x + '/match/' + x.match_id}
                  />
                )
              })
            }
          </tbody>
        </table>
      </div>

      <Dialog open={this.state.createModal} onClose={this.handlelose} aria-labelledby="form-dialog-title">
        <DialogTitle id="form-dialog-title">Subscribe</DialogTitle>
        <DialogContent>
          <CreateProject handleClose={this.handleClose}/>
        </DialogContent>
      </Dialog>
      </Paper>
    )
  }
}

export default withRouter(withStore(withStyles(style)(Projects)))







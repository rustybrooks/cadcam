import React from 'react'
import Paper from '@material-ui/core/Paper'
import { withStyles } from '@material-ui/core/styles'
import { withStore } from '../global-store'

const style = theme => ({
  'paper': {

  }
});


class Home extends React.Component {
  render() {
    const { classes } = this.props

    return (
     <div>
       <p>
         This is an unfiished but possibly still useful set of CAM stuff.  Right now this is mostly just routines
         to help automate creating CAM for printed circuit boards from Gerber files.  I have really only tested it with
         my own machines and my own gerber files, from the software I use, so there is very likely to be bugs or other
         problems.  I would love to hear from you if you have any questions.
       </p>

       <p>
         me@rustybrooks.com
       </p>
     </div>
    )
  }
}

export default withStore(withStyles(style)(Home))




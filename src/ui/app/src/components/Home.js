import React, { useEffect, useState } from 'react'
import * as material from '@material-ui/core'
import { Link } from 'react-router-dom'

import { withStyles } from '@material-ui/core/styles'
import { withStore } from '../global-store'

import Projects from './Projects'


const style = theme => ({
  'paper': {
    padding: theme.spacing(1),
  }
});


const Home = ({store, classes}) => {
  let [data, setData] = useState([])

  useEffect( () => {
    async function update() {
      let fw = store.get('frameworks')
      if (fw === null || fw === undefined) return
      setData(await fw.ProjectsApi.user_projects({limit: 100}))
    }
    update()
  }, [])


  return (
   <material.Paper className={classes.paper}>
     <br/>
     <material.Typography>
     This is an unfiished but possibly still useful set of CAM stuff.  Right now this is mostly just routines
     to help automate creating CAM for printed circuit boards from Gerber files.  I have really only tested it with
     my own machines and my own gerber files, from the software I use, so there is very likely to be bugs or other
     problems.  <a href='me@rustybrooks.com'>I would love to hear from you</a> if you have any questions.
     </material.Typography>

     <br/>
     <table border={1} cellPadding={5} cellSpacing={0}>
       <thead>
         <tr>
           <td>User</td>
           <td>Project count</td>
         </tr>
       </thead>
       <tbody>
         {
           data.map(x => <tr key={x.user_id}>
             <td>
               <Link to={'/projects/' + x.username}>{x.username}</Link>
             </td>
             <td align="right">{x.count}</td>
           </tr>)
         }
       </tbody>
     </table>
     <br/>

   </material.Paper>
  )
}

export default withStore(withStyles(style)(Home))




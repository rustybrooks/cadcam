class Framework {
  constructor(base_url, data) {
    // console.log(data)
    Object.keys(data).filter((k) => {
      return (k[0] !== '_')
    }).map((k) => {
      let cmd = data[k]
      const whole_url = base_url + '/' + cmd['simple_url']
      this[k] = (context) => {
        // console.log("posting ", JSON.stringify(context), "to", whole_url)
        fetch(whole_url, {
          method: 'POST',
          body: JSON.stringify(context),
          headers: {
            "Content-Type": "application/json; charset=utf-8",
          },
        }).then(
          (response) => {
            // console.log("response ok", response.ok)
            response.json().then(
              (json) => {
                return json
              }
            )
          },
          (err) => {
            console.log("ERROR!!", err)
          }
        )
      }
    })
  }
}

class Frameworks {
  constructor(base_url, framework_data) {
    // console.log(framework_data)
    Object.keys(framework_data).filter((k) => {
      return (k !== 'user')
    }).map((k) => {
      this[k] = new Framework(base_url, framework_data[k])
      return true;
    })
  }
}

let fetchFrameworks = (site, prefix) => {
  let url = site + prefix + '/framework/endpoints'

  return fetch(url)
    .then(response => response.json())
    .then(json => { return new Frameworks(site, json) })
}


export default fetchFrameworks
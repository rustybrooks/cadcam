import "regenerator-runtime/runtime";

class Framework {
  constructor(base_url, data, storage) {
    // console.log(data)
    Object.keys(data).filter((k) => {
      return (k[0] !== '_')
    }).map((k) => {
      let cmd = data[k]
      const whole_url = base_url + '/' + cmd['simple_url']

      let headers = {
        "Content-Type": "application/json; charset=utf-8",
      }
      const api_key = localStorage.getItem('api-key')

      console.log("api-key", api_key, api_key === null, api_key === "null")
      if (api_key) {
        headers["X-API-KEY"] = api_key
      }

      this[k] = (context) => {
        // console.log("posting ", JSON.stringify(context), "to", whole_url)
        return fetch(whole_url, {
          method: 'POST',
          body: JSON.stringify(context),
          headers: headers,
        }).then(response => {
          if (response.status === 403) {
            console.log("NO AUTH", storage.get('login-callback'))
            storage.get('login-widget').toggleDrawer(true)
            return null
          }
          return response.json()
        }).then((json) => { return json })
          .catch(error => {
            console.error("ERROR", error)
          });

      }
    })
  }
}

class Frameworks {
  constructor(base_url, framework_data, storage) {
    // console.log(framework_data)
    Object.keys(framework_data).filter((k) => {
      return (k !== 'user')
    }).map((k) => {
      this[k] = new Framework(base_url, framework_data[k], storage)
      return true;
    })
  }
}

let fetchFrameworks = (site, prefix, storage) => {
  let url = site + prefix + '/framework/endpoints'

  return fetch(url)
    .then(response => response.json())
    .then(json => { return new Frameworks(site, json, storage) })
}


export default fetchFrameworks
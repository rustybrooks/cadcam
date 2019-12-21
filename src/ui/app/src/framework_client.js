import "regenerator-runtime/runtime";

export class Status {
  constructor(status, details) {
    this.status = status
    this.details = details
  }
}


class Framework {
  constructor(base_url, data) {
    Object.keys(data).filter((k) => {
      return (k[0] !== '_')
    }).map((k) => {
      let cmd = data[k]
      const whole_url = base_url + '/' + cmd['simple_url']

      this[k] = async (context) => {
        let headers = {}

        const api_key = localStorage.getItem('api-key')
        if (api_key) {
          headers["X-API-KEY"] = api_key
        }

        let body = ""
        if (context instanceof FormData) {
          body = context
          console.log("We've got some form data here", body.getAll('file'), body.getAll('project_key'))
        } else {
          body = JSON.stringify(context)
          headers["Content-Type"] = "application/json; charset=utf-8"
        }

        // console.log("posting ", JSON.stringify(context), "to", whole_url)
        try {
          const response = await fetch(whole_url, {
            method: 'POST',
            body: body,
            headers: headers,
          })

          if (response.status === 500) {
            console.log('..... 500')
            return new Status(500, "A server error occurred")
          } else if (response.status === 400) {
            return new Status(400, await response.json())
          } else if (response.status === 403) {
            return new Status(403, await response.json())
          } else if (response.status === 404) {
            return new Status(404, "Not Found")
          }

          return response.json()
        } catch (e) {
          console.error(e);
          return new Status(500, "A server error occurred")
        } finally {
          console.log('We do cleanup here');
        }

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

  let headers = {}
  const api_key = localStorage.getItem('api-key')
  if (api_key) {
    headers["X-API-KEY"] = api_key
  }

  return fetch(url, {'headers': headers})
    .then(response => response.json())
    .then(json => { return new Frameworks(site, json, storage) })
}


export default fetchFrameworks

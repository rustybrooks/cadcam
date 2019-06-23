const hostname = window && window.location.origin;

console.log(hostname)
export let BASE_URL = null;
if (hostname.includes('cadcam')) {
  BASE_URL = hostname
} else {
  BASE_URL = hostname.split(":")[0] + ':' + hostname.split(":")[1] + ":5000"
}



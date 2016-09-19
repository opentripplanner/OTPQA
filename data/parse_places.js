const { createReadStream } = require('fs')
const readline = require('readline')
const http = require('http')
const fetch = require('node-fetch')

//console.log('name,lat,lon')

const TEMPLATE = 'http://dev-api.digitransit.fi/geocoding/v1/search?boundary.rect.min_lat=59.9&boundary.rect.max_lat=60.45&boundary.rect.min_lon=24.3&boundary.rect.max_lon=25.5&text='

const agent = new http.Agent({
  keepAlive: true,
  keepAliveMsecs: 60000,
  maxSockets: 2
});

readline.createInterface({
  input: createReadStream('reittiopas-geocoded-places-n-100.txt')
}).on('line', line =>
  fetch(`${TEMPLATE}${encodeURIComponent(line.split(/\s+\d+\s+/)[1])}`, {agent: agent})
    .then(res => {
      if (res.status === 200)
        return res.json()
        res.text().then(text => console.warn(text))
    })
    .then(data =>
      console.log(`"${data.features[0].properties.label}",${data.features[0].geometry.coordinates[1]},${data.features[0].geometry.coordinates[0]}`)
      //data.features[0].properties.label.toLowerCase() === line.split(/\s+\d+\s+/)[1].toLowerCase() || console.log(line.split(/\s+\d+\s+/)[1] + " => " + data.features[0].properties.label)
    )
    .catch((err) => console.warn(err))
)

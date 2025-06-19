const dns = require('dns')
dns.resolve('www.globo.com', callback=(err, result) => {

if (err) {
    console.error(`erro: ${err}`)
  } else {
    console.log(result)
  }
});

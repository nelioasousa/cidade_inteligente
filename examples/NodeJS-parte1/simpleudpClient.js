var args = process.argv.slice(2);
var dgram = require('dgram');
var PORT = 7895;
var HOST = args[1];
var message = args[0];

var client = dgram.createSocket('udp4');

client.send(message, 0, message.length, PORT, HOST, function() {
  console.info(`Msg enviada: ${message}`);
});

client.on("message", function(message, rinfo) {
  console.info(`Msg recebida:  ${message}`);
  client.close();
});

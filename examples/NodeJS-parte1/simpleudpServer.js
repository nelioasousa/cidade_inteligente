var PORT = 7895;
var HOST = '127.0.0.1';
var i = 1

var dgram = require('dgram');
var server = dgram.createSocket('udp4');

server.on('listening', function() {
  console.info(`Esperando Msg ${i} ...`);
});

server.on('message', function(message, remote) {
 
 var msg = message.toString();
 msg = msg.toUpperCase();
 server.send(msg, 0, message.length, remote.port, remote.address);
 console.info(`Cliente: ${remote.address} - Porta: ${remote.port}`);
 console.info(`Msg: ${message}`);
 i+=1
 console.info(`Esperando Msg ${i} ...`);
});

server.bind(PORT, HOST);

const Net = require('net');
var readline = require('readline');
const port = 7895;
const host = 'localhost';

const client = new Net.Socket();

client.connect({ port: port, host: host }, function() {
    var input = readline.createInterface({
	    input: process.stdin,
	    output: process.stdout
    });

    input.question("O que você quer escrever?\n", function(resp){
	    
      console.info(`Msg enviada: ${resp}`);
      client.write(resp);
      client.on('data', function(message) {
        console.info(`Msg recebida: ${message}`);    
        client.end();
      });
      input.close();
    });  
});





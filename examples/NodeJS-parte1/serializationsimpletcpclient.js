const Pessoa = require('./pessoa');
const Net = require('net');
const port = 7895;
const host = 'localhost';

const client = new Net.Socket();

client.connect({ port: port, host: host }, function() {
    var pessoa = new Pessoa("Joao da Silva", 'Quixada', '999990000', '2014');
    console.info(pessoa.toString());
    var pessoa_string = JSON.stringify(pessoa)
    client.write(pessoa_string);
    client.on('data', function(message) {
      var pessoa_obj = JSON.parse(message);
      pessoa = new Pessoa(pessoa_obj.nome, pessoa_obj.cidade, pessoa_obj.telefone, pessoa_obj.ano);
 
      console.info(pessoa.toString());  
      client.end();
    });
});





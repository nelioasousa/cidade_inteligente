const Net = require('net');
const port = 7895;
const server = new Net.Server();

server.listen(port, function() {
    console.log(`Servidor conectado na porta ${port}`);
});


server.on('connection', function(socket) {
    socket.on('data', function(obj) {
	var pessoa_obj = JSON.parse(obj);
        pessoa_obj.cidade = "Fortaleza";
	pessoa_obj.ano = '2019';
        var pessoa_str = JSON.stringify(pessoa_obj)
        socket.write(pessoa_str);
	
    });

    socket.on('end', function() {
        console.log('Cliente desconectado');
    });

    socket.on('error', function(err) {
        console.log(`Erro ocorrido: ${err}`);
    });
});






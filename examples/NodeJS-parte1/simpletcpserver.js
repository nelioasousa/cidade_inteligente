const Net = require('net');
const port = 7895;
const server = new Net.Server();

server.listen(port, function() {
    console.log(`Servidor conectado na porta ${port}`);
});

server.on('connection', function(socket) {
    socket.on('data', function(message) {
	var msg = message.toString();
	msg = msg.toUpperCase();
	socket.write(msg);
    });

    socket.on('end', function() {
        console.log('Cliente desconectado');
    });

    socket.on('error', function(err) {
        console.log(`Erro ocorrido: ${err}`);
    });
});
